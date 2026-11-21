from src.judge.sandbox import (
    STATUS_MEMORY_EXCEEDED,
    STATUS_RUNTIME_ERROR,
    STATUS_SUCCESS,
    STATUS_TIMEOUT,
    SandboxRunner,
)


def test_sandbox_success():
    runner = SandboxRunner()
    result = runner.run("print('hello from sandbox')")

    assert result.status == STATUS_SUCCESS
    assert "hello from sandbox" in result.stdout
    assert result.exit_code == 0


def test_sandbox_timeout():
    runner = SandboxRunner()
    result = runner.run("while True: pass", timeout=1.0)

    assert result.status == STATUS_TIMEOUT
    assert result.timed_out is True


def test_sandbox_memory_limit():
    runner = SandboxRunner()
    # Allocating a massive string to trigger OOM / exit code 137 under 64MB limit
    code = "a = ' ' * (200 * 1024 * 1024)"  
    result = runner.run(code, memory_limit="64m")
    
    assert result.status == STATUS_MEMORY_EXCEEDED or result.exit_code == 137

def test_sandbox_stdin_sum():
    runner = SandboxRunner()
    code = "print(sum(map(int, input().split())))"
    result = runner.run(code, stdin="1 2 3\n")

    assert result.status == STATUS_SUCCESS
    assert result.exit_code == 0
    assert result.stdout.strip() == "6"
    assert result.stderr == ""

def test_sandbox_empty_stdin_no_read():
    runner = SandboxRunner()
    result = runner.run("print('ok')", stdin="", timeout=2.0)

    assert result.status == STATUS_SUCCESS
    assert result.timed_out is False
    assert result.exit_code == 0
    assert result.stdout.strip() == "ok"

def test_sandbox_reads_missing_stdin_errors_not_hangs():
    runner = SandboxRunner()
    result = runner.run("input()", stdin="", timeout=2.0)

    assert result.timed_out is False
    assert result.status == STATUS_RUNTIME_ERROR
    assert result.exit_code != 0
    assert "EOFError" in result.stderr

def test_sandbox_stderr_separated_from_stdout():
    runner = SandboxRunner()
    code = "print('visible stdout')\nraise ValueError('boom on stderr')"
    result = runner.run(code)

    assert result.status == STATUS_RUNTIME_ERROR
    assert result.exit_code != 0
    assert "visible stdout" in result.stdout
    assert "boom on stderr" not in result.stdout
    assert "ValueError: boom on stderr" in result.stderr