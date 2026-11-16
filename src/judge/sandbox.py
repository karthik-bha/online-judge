import time
from dataclasses import dataclass

import docker
from docker.errors import APIError, DockerException
from requests.exceptions import ReadTimeout, RequestException

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
    output: str
    execution_time: float
    timed_out: bool

class SandboxRunner:
    def __init__(self, image: str = "python:3.12-slim"):
        self.client = docker.from_env()
        self.image = image

    def run(self, code: str, timeout: float = 2.0, memory_limit: str = "128m") -> SandboxResult:
        """
        Executes untrusted Python code inside an isolated, hardened Docker container.
        Enforces resource limits, read-only filesystems, network isolation, and hard timeout reaping.
        """
        container = None
        start_time = time.time()

        try:
            # create container with security flags
            container = self.client.containers.create(
                image=self.image,
                command=["python", "-c", code],
                network_mode="none",
                read_only=True,
                mem_limit=memory_limit,
                pids_limit=64,
                cap_drop=["ALL"],
                security_opt=["no-new-privileges"],
                tmpfs={"/tmp": "rw,noexec,nosuid,size=64m"},
                user="1000:1000"
            )

            container.start()

            # wait for wall clock timeout 
            timed_out = False
            exit_code = -1
            try:
                result = container.wait(timeout=timeout)
                exit_code = result.get("StatusCode", -1)
            except (ReadTimeout, RequestException, APIError):
                timed_out = True
                try:
                    container.kill()
                except Exception:  # noqa: S110, BLE001
                    pass
                exit_code = -9

            execution_time = time.time() - start_time

            # collect logs 
            logs = container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace")

            # check status using correct uppercase constants
            if timed_out:
                status = STATUS_TIMEOUT
            elif exit_code == 137:
                status = STATUS_MEMORY_EXCEEDED
            elif exit_code != 0:
                status = STATUS_RUNTIME_ERROR
            else:
                status = STATUS_SUCCESS
            
            return SandboxResult(
                status=status,
                exit_code=exit_code,
                output=logs,
                execution_time=round(execution_time, 4),
                timed_out=timed_out
            )
        
        except DockerException as e:
            execution_time = time.time() - start_time
            return SandboxResult(
                status=STATUS_SYSTEM_ERROR,
                exit_code=-1,
                output=str(e),
                execution_time=round(execution_time, 4),
                timed_out=False
            )

        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception:  # noqa: S110, BLE001
                    pass