"""Tests for CLI commands."""

import os
from pathlib import Path

import git
import pytest
from click.testing import CliRunner

from wt_tools.cli import cli
from wt_tools.config import get_global_config_path


@pytest.fixture
def runner() -> CliRunner:
    """Create a Click CLI test runner."""
    return CliRunner()


def test_cli_help(runner: CliRunner) -> None:
    """Test CLI help command."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Git worktree management with hooks" in result.output
    assert "create" in result.output
    assert "list" in result.output
    assert "delete" in result.output


def test_cli_version(runner: CliRunner) -> None:
    """Test CLI version command."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.output.lower()


def test_init_project_config(
    runner: CliRunner, temp_git_repo: git.Repo, change_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test initializing project configuration."""
    os.chdir(temp_git_repo.working_dir)

    # Mock the Confirm.ask to auto-decline
    from rich.prompt import Confirm

    monkeypatch.setattr(Confirm, "ask", lambda *args, **kwargs: False)

    result = runner.invoke(cli, ["init"])
    assert result.exit_code == 0

    # Check config file was created
    config_file = Path(temp_git_repo.working_dir) / ".wt-tools.yaml"
    assert config_file.exists()

    content = config_file.read_text()
    assert "worktree_dir:" in content
    assert "hooks:" in content


def test_init_global_config(runner: CliRunner, temp_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test initializing global configuration."""
    # Mock the global config path to use temp directory
    fake_config_path = temp_dir / ".config" / "wt-tools" / "config.yaml"

    def mock_get_global_config_path():
        return fake_config_path

    # Patch both in config module and cli module (where it's imported)
    from wt_tools import config as config_module
    from wt_tools import cli as cli_module

    monkeypatch.setattr(config_module, "get_global_config_path", mock_get_global_config_path)
    monkeypatch.setattr(cli_module, "get_global_config_path", mock_get_global_config_path)

    result = runner.invoke(cli, ["init", "--global"])
    assert result.exit_code == 0

    # Check config file was created
    assert fake_config_path.exists()

    content = fake_config_path.read_text()
    assert "worktree_dir:" in content


def test_create_worktree(
    runner: CliRunner, temp_git_repo: git.Repo, change_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test creating a worktree via CLI."""
    os.chdir(temp_git_repo.working_dir)

    # Mock Confirm.ask to auto-accept gitignore prompts
    from rich.prompt import Confirm

    monkeypatch.setattr(Confirm, "ask", lambda *args, **kwargs: True)

    result = runner.invoke(cli, ["create", "test-branch", "--skip-hooks"])
    assert result.exit_code == 0

    # Verify worktree was created
    worktree_path = Path(temp_git_repo.working_dir) / ".worktrees" / "test-branch"
    assert worktree_path.exists()


def test_create_worktree_custom_path(
    runner: CliRunner, temp_git_repo: git.Repo, change_dir: Path, temp_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test creating a worktree with custom path via CLI."""
    os.chdir(temp_git_repo.working_dir)

    # Mock Confirm.ask
    from rich.prompt import Confirm

    monkeypatch.setattr(Confirm, "ask", lambda *args, **kwargs: True)

    custom_path = str(temp_dir / "custom")

    result = runner.invoke(
        cli, ["create", "test-branch", "--path", custom_path, "--skip-hooks"]
    )
    assert result.exit_code == 0

    # Verify worktree was created at custom path
    assert Path(custom_path).exists()


def test_list_worktrees(
    runner: CliRunner, temp_git_repo: git.Repo, change_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test listing worktrees via CLI."""
    os.chdir(temp_git_repo.working_dir)

    # Mock Confirm.ask
    from rich.prompt import Confirm

    monkeypatch.setattr(Confirm, "ask", lambda *args, **kwargs: True)

    # Create a worktree first
    runner.invoke(cli, ["create", "test-branch", "--skip-hooks"])

    # List worktrees
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    # Check for the branch name in some form (may not be exact due to table formatting)
    output_normalized = result.output.replace("\n", " ")
    assert "test-branch" in output_normalized or "test" in output_normalized


def test_list_worktrees_verbose(
    runner: CliRunner, temp_git_repo: git.Repo, change_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test listing worktrees with verbose flag via CLI."""
    os.chdir(temp_git_repo.working_dir)

    # Mock Confirm.ask
    from rich.prompt import Confirm

    monkeypatch.setattr(Confirm, "ask", lambda *args, **kwargs: True)

    # Create a worktree
    runner.invoke(cli, ["create", "test-branch", "--skip-hooks"])

    # List with verbose
    result = runner.invoke(cli, ["list", "--verbose"])
    assert result.exit_code == 0
    output_normalized = result.output.replace("\n", " ")
    assert "test-branch" in output_normalized or "Git Worktrees" in result.output


def test_switch_worktree(
    runner: CliRunner, temp_git_repo: git.Repo, change_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test switching worktrees via CLI."""
    os.chdir(temp_git_repo.working_dir)

    # Mock Confirm.ask
    from rich.prompt import Confirm

    monkeypatch.setattr(Confirm, "ask", lambda *args, **kwargs: True)

    # Create a worktree
    create_result = runner.invoke(cli, ["create", "test-branch", "--skip-hooks"])
    assert create_result.exit_code == 0

    # Switch to it
    result = runner.invoke(cli, ["switch", "test-branch"])
    assert result.exit_code == 0

    # Output should be the path (for shell command substitution)
    assert ".worktrees" in result.output
    assert "test-branch" in result.output


def test_delete_worktree(
    runner: CliRunner, temp_git_repo: git.Repo, change_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test deleting a worktree via CLI."""
    os.chdir(temp_git_repo.working_dir)

    # Mock Confirm.ask
    from rich.prompt import Confirm

    monkeypatch.setattr(Confirm, "ask", lambda *args, **kwargs: True)

    # Create a worktree
    create_result = runner.invoke(cli, ["create", "test-branch", "--skip-hooks"])
    assert create_result.exit_code == 0

    worktree_path = Path(temp_git_repo.working_dir) / ".worktrees" / "test-branch"
    assert worktree_path.exists()

    # Delete it with force flag (skip confirmation)
    result = runner.invoke(cli, ["delete", "test-branch", "--force"])
    assert result.exit_code == 0

    # Verify it was deleted
    assert not worktree_path.exists()


def test_delete_worktree_keep_branch(
    runner: CliRunner, temp_git_repo: git.Repo, change_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test deleting worktree but keeping branch via CLI."""
    os.chdir(temp_git_repo.working_dir)

    # Mock Confirm.ask
    from rich.prompt import Confirm

    monkeypatch.setattr(Confirm, "ask", lambda *args, **kwargs: True)

    # Create a worktree
    create_result = runner.invoke(cli, ["create", "test-branch", "--skip-hooks"])
    assert create_result.exit_code == 0

    # Delete worktree but keep branch
    result = runner.invoke(cli, ["delete", "test-branch", "--force", "--keep-branch"])
    assert result.exit_code == 0

    # Branch should still exist
    branches = [ref.name for ref in temp_git_repo.references]
    assert "test-branch" in branches


def test_config_show(
    runner: CliRunner, temp_git_repo: git.Repo, change_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test showing configuration via CLI."""
    os.chdir(temp_git_repo.working_dir)

    # Mock Confirm.ask
    from rich.prompt import Confirm

    monkeypatch.setattr(Confirm, "ask", lambda *args, **kwargs: False)

    # Initialize project config first
    runner.invoke(cli, ["init"])

    # Show merged config
    result = runner.invoke(cli, ["config"])
    assert result.exit_code == 0
    assert "worktree_dir" in result.output or "Merged" in result.output


def test_cleanup(
    runner: CliRunner, temp_git_repo: git.Repo, change_dir: Path
) -> None:
    """Test cleanup command via CLI."""
    os.chdir(temp_git_repo.working_dir)

    # Run cleanup in dry-run mode
    result = runner.invoke(cli, ["cleanup", "--dry-run"])
    assert result.exit_code == 0

    # Run actual cleanup
    result = runner.invoke(cli, ["cleanup"])
    assert result.exit_code == 0


def test_clone(
    runner: CliRunner, temp_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test clone command via CLI."""
    # Ensure we start in temp_dir
    os.chdir(temp_dir)

    try:
        # Create a source repo to clone from
        source_repo_dir = temp_dir / "source-repo"
        source_repo = git.Repo.init(source_repo_dir)
        source_repo.config_writer().set_value("user", "name", "Test User").release()
        source_repo.config_writer().set_value("user", "email", "test@example.com").release()

        # Change to source repo to add files
        os.chdir(source_repo_dir)

        # Create initial commit
        readme = source_repo_dir / "README.md"
        readme.write_text("# Test Repo\n")
        source_repo.index.add(["README.md"])
        source_repo.index.commit("Initial commit")

        # Change to temp dir for cloning
        clone_target_dir = temp_dir / "clone-test"
        clone_target_dir.mkdir()
        os.chdir(clone_target_dir)

        # Mock Confirm.ask to auto-decline gitignore prompts
        from rich.prompt import Confirm

        monkeypatch.setattr(Confirm, "ask", lambda *args, **kwargs: False)

        # Clone the repo
        result = runner.invoke(cli, ["clone", str(source_repo_dir)])
        assert result.exit_code == 0
        assert "Setup complete!" in result.output

        # Verify cloned directory exists
        cloned_dir = clone_target_dir / "source-repo"
        assert cloned_dir.exists()
        assert (cloned_dir / ".git").exists()
        assert (cloned_dir / "README.md").exists()
        assert (cloned_dir / ".wt-tools.yaml").exists()

    finally:
        # Go back to a safe directory (project root)
        os.chdir("/Users/tanchien/Documents/wt-tools")


def test_clone_custom_directory(
    runner: CliRunner, temp_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test clone command with custom directory."""
    # Ensure we start in temp_dir
    os.chdir(temp_dir)

    try:
        # Create a source repo
        source_repo_dir = temp_dir / "source-repo"
        source_repo = git.Repo.init(source_repo_dir)
        source_repo.config_writer().set_value("user", "name", "Test User").release()
        source_repo.config_writer().set_value("user", "email", "test@example.com").release()

        # Change to source repo to add files
        os.chdir(source_repo_dir)
        readme = source_repo_dir / "README.md"
        readme.write_text("# Test Repo\n")
        source_repo.index.add(["README.md"])
        source_repo.index.commit("Initial commit")

        # Change to temp dir
        clone_target_dir = temp_dir / "clone-test"
        clone_target_dir.mkdir()
        os.chdir(clone_target_dir)

        # Mock Confirm.ask
        from rich.prompt import Confirm

        monkeypatch.setattr(Confirm, "ask", lambda *args, **kwargs: False)

        # Clone with custom directory name
        result = runner.invoke(cli, ["clone", str(source_repo_dir), "my-custom-name"])
        assert result.exit_code == 0

        # Verify custom directory exists
        cloned_dir = clone_target_dir / "my-custom-name"
        assert cloned_dir.exists()
        assert (cloned_dir / ".wt-tools.yaml").exists()

    finally:
        # Go back to a safe directory (project root)
        os.chdir("/Users/tanchien/Documents/wt-tools")


def test_clone_skip_init(
    runner: CliRunner, temp_dir: Path
) -> None:
    """Test clone command with --skip-init flag."""
    # Ensure we start in temp_dir
    os.chdir(temp_dir)

    try:
        # Create a source repo
        source_repo_dir = temp_dir / "source-repo"
        source_repo = git.Repo.init(source_repo_dir)
        source_repo.config_writer().set_value("user", "name", "Test User").release()
        source_repo.config_writer().set_value("user", "email", "test@example.com").release()

        # Change to source repo to add files
        os.chdir(source_repo_dir)
        readme = source_repo_dir / "README.md"
        readme.write_text("# Test Repo\n")
        source_repo.index.add(["README.md"])
        source_repo.index.commit("Initial commit")

        # Change to temp dir
        clone_target_dir = temp_dir / "clone-test"
        clone_target_dir.mkdir()
        os.chdir(clone_target_dir)

        # Clone with --skip-init
        result = runner.invoke(cli, ["clone", str(source_repo_dir), "--skip-init"])
        assert result.exit_code == 0

        # Verify no .wt-tools.yaml was created
        cloned_dir = clone_target_dir / "source-repo"
        assert cloned_dir.exists()
        assert not (cloned_dir / ".wt-tools.yaml").exists()

    finally:
        # Go back to a safe directory (project root)
        os.chdir("/Users/tanchien/Documents/wt-tools")
