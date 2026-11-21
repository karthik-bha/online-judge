import logging
import socket
import time
from dataclasses import dataclass

import docker
from docker.errors import APIError, DockerException
from requests.exceptions import ReadTimeout, RequestException
from urllib3.exceptions import ReadTimeoutError

logger = logging.getLogger(__name__)

# Status Constants
STATUS_SUCCESS = "SUCCESS"
STATUS_TIMEOUT = "TIMEOUT"
STATUS_MEMORY_EXCEEDED = "MEMORY_LIMIT_EXCEEDED"
STATUS_RUNTIME_ERROR = "RUNTIME_ERROR"
STATUS_SYSTEM_ERROR = "SYSTEM_ERROR"

@dataclass
class SandboxResult:
    status: str
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    timed_out: bool
    cleanup_error: str | None = None

def _is_wait_timeout(exc: BaseException) -> bool:
    seen: set[int] = set()
    stack: list[BaseException | None] = [exc, exc.__cause__, exc.__context__]

    while stack:
        cur = stack.pop()
        if cur is None or id(cur) in seen:
            continue
        seen.add(id(cur))

        if isinstance(cur, ReadTimeout | ReadTimeoutError | TimeoutError):
            return True
        if "timed out" in str(cur).lower():
            return True

        stack.extend([cur.__cause__, cur.__context__])

    logger.debug("Non-timeout wait error chain: %r (cause=%r, context=%r)", exc, exc.__cause__, exc.__context__)
    return False

def _shutdown_write_and_close(sock_wrapper: object)-> None:
    if sock_wrapper is None:
        return
    raw_sock= getattr(sock_wrapper, "_sock", sock_wrapper)
    if hasattr(raw_sock, "shutdown"):
        try:
            raw_sock.shutdown(socket.SHUT_WR)
        except OSError as exc:
            logger.debug("Failed to shutdown write side of stdin socket: %s", exc)
    close_fn= getattr(sock_wrapper, "close", None)
    if callable(close_fn):
        try:
            close_fn()
        except OSError as exc:
            logger.debug("Failed to close stdin socket: %s", exc)

class SandboxRunner:
    def __init__(self, image: str = "python:3.12-slim"):
        self.client = docker.from_env()
        self.image = image

    def run(
        self, 
        code: str, 
        stdin: str = "", 
        timeout: float = 2.0, 
        memory_limit: str = "128m"
        ) -> SandboxResult:
        """
        Executes untrusted Python code inside an isolated, hardened Docker container.
        Enforces resource limits, read-only filesystems, network isolation, and hard timeout reaping.
        """
        container= None
        stdin_sock= None
        cleanup_errors: list[str] = []
        start_time= time.monotonic()

        try:
            # create container with security flags
            container = self.client.containers.create(
                image=self.image,
                command=["python", "-c", code],
                network_mode="none",
                read_only=True,
                mem_limit=memory_limit,
                memswap_limit=memory_limit,
                pids_limit=64,
                cap_drop=["ALL"],
                security_opt=["no-new-privileges"],
                tmpfs={"/tmp": "rw,noexec,nosuid,size=64m"},
                user="1000:1000",
                stdin_open=True,
            )

            stdin_sock= container.attach_socket(params={"stdin":1, "stream":1})
            container.start()

            if stdin:
                raw_sock= getattr(stdin_sock, "_sock", stdin_sock)
                raw_sock.sendall(stdin.encode("utf-8"))
            
            _shutdown_write_and_close(stdin_sock)
            stdin_sock= None

            # wait for wall clock timeout 
            timed_out= False
            exit_code= -1
            try:
                result = container.wait(timeout=timeout)
                exit_code = result.get("StatusCode", -1)
            except (ReadTimeout, RequestException) as exc:
                if not _is_wait_timeout(exc):
                    raise
                timed_out = True
                try:
                    container.kill()
                except APIError as kill_exc:
                    msg = f"Failed to kill timed-out container {container.short_id}: {kill_exc}"
                    logger.warning(msg)
                    cleanup_errors.append(msg)
                exit_code = -9

            execution_time = time.monotonic() - start_time

            # collect logs 
            stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
            stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")

            # check status using correct uppercase constants
            if timed_out:
                status = STATUS_TIMEOUT
            elif exit_code == 137:
                status = STATUS_MEMORY_EXCEEDED
            elif exit_code != 0:
                status = STATUS_RUNTIME_ERROR
            else:
                status = STATUS_SUCCESS
            
        except (DockerException, RequestException, OSError) as exc:
            execution_time = time.monotonic() - start_time
            status = STATUS_SYSTEM_ERROR
            exit_code = -1
            stdout = ""
            stderr = str(exc)
            timed_out = False

        finally:
            _shutdown_write_and_close(stdin_sock)
            if container:
                try:
                    container.remove(force=True)
                except APIError as rm_exc:
                    msg = f"Failed to remove container {container.short_id}: {rm_exc}"
                    logger.warning(msg)
                    cleanup_errors.append(msg)

        return SandboxResult(
            status=status,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            execution_time=round(execution_time, 4),
            timed_out=timed_out,
            cleanup_error="; ".join(cleanup_errors) if cleanup_errors else None,
        )