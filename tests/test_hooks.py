"""Tests for hook execution."""

import pytest

from wt_tools.config import HookConfig
from wt_tools.hooks import HookExecutionError, execute_hooks, run_hook


def test_run_hook_success() -> None:
    """Test running a successful hook."""
    hook = HookConfig(
        name="Echo test",
        command="echo 'Hello World'",
        working_dir="/tmp",
        timeout=10,
        on_failure="abort",
    )

    context = {"path": "/tmp", "branch": "test"}

    result = run_hook(hook, context)
    assert result is True


def test_run_hook_failure() -> None:
    """Test running a failing hook."""
    hook = HookConfig(
        name="Fail test",
        command="exit 1",
        working_dir="/tmp",
        timeout=10,
        on_failure="abort",
    )

    context = {"path": "/tmp", "branch": "test"}

    result = run_hook(hook, context)
    assert result is False


def test_run_hook_timeout() -> None:
    """Test hook timeout."""
    hook = HookConfig(
        name="Timeout test",
        command="sleep 10",
        working_dir="/tmp",
        timeout=1,  # 1 second timeout
        on_failure="abort",
    )

    context = {"path": "/tmp", "branch": "test"}

    result = run_hook(hook, context)
    assert result is False


def test_run_hook_variable_substitution(temp_dir) -> None:
    """Test variable substitution in hook commands."""
    hook = HookConfig(
        name="Variable test",
        command="echo '{branch}' > {path}/test.txt",
        working_dir="{path}",
        timeout=10,
        on_failure="abort",
    )

    context = {"path": str(temp_dir), "branch": "feature/test"}

    result = run_hook(hook, context)
    assert result is True

    # Check if file was created with correct content
    test_file = temp_dir / "test.txt"
    assert test_file.exists()
    content = test_file.read_text().strip()
    assert "feature/test" in content


def test_run_hook_env_variables(temp_dir) -> None:
    """Test environment variable support in hooks."""
    hook = HookConfig(
        name="Env test",
        command="echo $TEST_VAR > {path}/env.txt",
        working_dir="{path}",
        timeout=10,
        env={"TEST_VAR": "test_value_{branch}"},
        on_failure="abort",
    )

    context = {"path": str(temp_dir), "branch": "test"}

    result = run_hook(hook, context)
    assert result is True

    # Check environment variable was set
    env_file = temp_dir / "env.txt"
    assert env_file.exists()
    content = env_file.read_text().strip()
    assert "test_value_test" in content


def test_execute_hooks_all_success() -> None:
    """Test executing multiple successful hooks."""
    hooks = [
        HookConfig(name="Hook 1", command="echo 'test1'", on_failure="abort"),
        HookConfig(name="Hook 2", command="echo 'test2'", on_failure="abort"),
        HookConfig(name="Hook 3", command="echo 'test3'", on_failure="abort"),
    ]

    context = {"path": "/tmp", "branch": "test"}

    # Should not raise
    execute_hooks("post_create", hooks, context)


def test_execute_hooks_abort_on_failure() -> None:
    """Test hook execution aborts on failure when on_failure='abort'."""
    hooks = [
        HookConfig(name="Hook 1", command="echo 'test1'", on_failure="abort"),
        HookConfig(name="Hook 2", command="exit 1", on_failure="abort"),
        HookConfig(
            name="Hook 3", command="echo 'test3'", on_failure="abort"
        ),  # Should not run
    ]

    context = {"path": "/tmp", "branch": "test"}

    with pytest.raises(HookExecutionError, match="Hook 'Hook 2' failed"):
        execute_hooks("post_create", hooks, context)


def test_execute_hooks_continue_on_failure() -> None:
    """Test hook execution continues when on_failure='continue'."""
    hooks = [
        HookConfig(name="Hook 1", command="echo 'test1'", on_failure="continue"),
        HookConfig(name="Hook 2", command="exit 1", on_failure="continue"),
        HookConfig(
            name="Hook 3", command="echo 'test3'", on_failure="continue"
        ),  # Should still run
    ]

    context = {"path": "/tmp", "branch": "test"}

    # Should not raise even though Hook 2 failed
    execute_hooks("post_create", hooks, context)


def test_execute_hooks_warn_on_failure() -> None:
    """Test hook execution warns but continues when on_failure='warn'."""
    hooks = [
        HookConfig(name="Hook 1", command="echo 'test1'", on_failure="warn"),
        HookConfig(name="Hook 2", command="exit 1", on_failure="warn"),
        HookConfig(name="Hook 3", command="echo 'test3'", on_failure="warn"),
    ]

    context = {"path": "/tmp", "branch": "test"}

    # Should not raise even though Hook 2 failed
    execute_hooks("post_create", hooks, context)


def test_execute_hooks_empty_list() -> None:
    """Test executing empty hook list."""
    hooks = []
    context = {"path": "/tmp", "branch": "test"}

    # Should not raise
    execute_hooks("post_create", hooks, context)


def test_run_hook_nonexistent_working_dir() -> None:
    """Test hook with non-existent working directory."""
    hook = HookConfig(
        name="Bad dir test",
        command="echo 'test'",
        working_dir="/nonexistent/directory",
        timeout=10,
        on_failure="abort",
    )

    context = {"path": "/tmp", "branch": "test"}

    result = run_hook(hook, context)
    assert result is False
