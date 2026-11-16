from src.judge.sandbox import (
    STATUS_MEMORY_EXCEEDED,
    STATUS_SUCCESS,
    STATUS_TIMEOUT,
    SandboxRunner,
)


def test_sandbox_success():
    runner = SandboxRunner()
    result = runner.run("print('hello from sandbox')")

    assert result.status == STATUS_SUCCESS
    assert "hello from sandbox" in result.output
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