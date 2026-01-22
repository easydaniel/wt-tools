"""Tests for worktree operations."""

import os
from pathlib import Path

import git
import pytest

from wt_tools.config import Config, Settings
from wt_tools.worktree import (
    create_worktree,
    find_worktree_by_branch,
    format_size,
    get_directory_size,
    get_project_name,
    get_repo,
    get_worktree_status,
    get_worktrees,
    resolve_worktree_path,
    sanitize_branch_name,
)


def test_get_repo(temp_git_repo: git.Repo, change_dir: Path) -> None:
    """Test getting git repository."""
    os.chdir(temp_git_repo.working_dir)
    repo = get_repo()
    assert repo.working_dir == temp_git_repo.working_dir


def test_get_repo_not_in_git(temp_dir: Path, change_dir: Path) -> None:
    """Test get_repo when not in a git repository."""
    os.chdir(temp_dir)
    with pytest.raises(SystemExit):
        get_repo()


def test_get_project_name(temp_git_repo: git.Repo) -> None:
    """Test getting project name from repository."""
    name = get_project_name(temp_git_repo)
    assert name == Path(temp_git_repo.working_dir).name


def test_sanitize_branch_name() -> None:
    """Test sanitizing branch names for directory names."""
    assert sanitize_branch_name("feature/new-feature") == "feature-new-feature"
    assert sanitize_branch_name("bugfix\\issue-123") == "bugfix-issue-123"
    assert sanitize_branch_name("simple-branch") == "simple-branch"


def test_resolve_worktree_path(temp_git_repo: git.Repo) -> None:
    """Test resolving worktree paths."""
    config = Config(
        worktree_dir=".worktrees/{branch}",
        worktree_dir_fallback="~/.worktrees/{project}/{branch}",
    )

    # Primary path
    path = resolve_worktree_path("feature/test", config, temp_git_repo, use_fallback=False)
    assert ".worktrees" in str(path)
    assert "feature-test" in str(path)

    # Fallback path
    fallback_path = resolve_worktree_path("feature/test", config, temp_git_repo, use_fallback=True)
    assert ".worktrees" in str(fallback_path)
    assert "feature-test" in str(fallback_path)
    assert get_project_name(temp_git_repo) in str(fallback_path)


def test_get_worktrees(temp_git_repo: git.Repo, change_dir: Path) -> None:
    """Test getting list of worktrees."""
    os.chdir(temp_git_repo.working_dir)

    # Initially just main worktree
    worktrees = get_worktrees(temp_git_repo)
    assert len(worktrees) >= 1

    # Create a new worktree
    worktree_path = Path(temp_git_repo.working_dir) / ".worktrees" / "test-branch"
    temp_git_repo.git.worktree("add", "-b", "test-branch", str(worktree_path))

    # Should now have 2 worktrees
    worktrees = get_worktrees(temp_git_repo)
    # Note: main worktree might be marked as bare in some cases
    assert len(worktrees) >= 2


def test_find_worktree_by_branch(temp_git_repo: git.Repo, change_dir: Path) -> None:
    """Test finding worktree by branch name."""
    os.chdir(temp_git_repo.working_dir)

    # Create worktree
    worktree_path = Path(temp_git_repo.working_dir) / ".worktrees" / "test-branch"
    temp_git_repo.git.worktree("add", "-b", "test-branch", str(worktree_path))

    worktrees = get_worktrees(temp_git_repo)

    # Find existing branch
    found = find_worktree_by_branch("test-branch", worktrees)
    assert found is not None
    assert found.branch == "test-branch"

    # Non-existent branch
    not_found = find_worktree_by_branch("non-existent", worktrees)
    assert not_found is None


def test_get_worktree_status(temp_git_repo: git.Repo, change_dir: Path) -> None:
    """Test getting worktree status."""
    os.chdir(temp_git_repo.working_dir)

    # Clean worktree
    status = get_worktree_status(Path(temp_git_repo.working_dir))
    assert status == "clean"

    # Create untracked file
    test_file = Path(temp_git_repo.working_dir) / "test.txt"
    test_file.write_text("test")

    status = get_worktree_status(Path(temp_git_repo.working_dir))
    assert status == "modified"


def test_get_directory_size(temp_dir: Path) -> None:
    """Test calculating directory size."""
    # Empty directory
    size = get_directory_size(temp_dir)
    assert size == 0

    # Add some files
    (temp_dir / "file1.txt").write_text("a" * 100)
    (temp_dir / "file2.txt").write_text("b" * 200)

    size = get_directory_size(temp_dir)
    assert size == 300


def test_format_size() -> None:
    """Test formatting size in bytes."""
    assert format_size(0) == "0.0 B"
    assert format_size(512) == "512.0 B"
    assert format_size(1024) == "1.0 KB"
    assert format_size(1024 * 1024) == "1.0 MB"
    assert format_size(1024 * 1024 * 1024) == "1.0 GB"


def test_create_worktree_new_branch(
    temp_git_repo: git.Repo, change_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test creating worktree with new branch."""
    os.chdir(temp_git_repo.working_dir)

    # Mock Confirm.ask
    from rich.prompt import Confirm

    monkeypatch.setattr(Confirm, "ask", lambda *args, **kwargs: True)

    config = Config(
        worktree_dir=".worktrees/{branch}",
        hooks={"post_create": [], "pre_switch": [], "post_delete": []},
        settings=Settings(confirm_delete=False),
    )

    # Create worktree
    worktree_path = create_worktree("feature/new", skip_hooks=True, config=config)

    assert worktree_path.exists()
    assert "feature-new" in str(worktree_path)

    # Verify worktree was created
    worktrees = get_worktrees(temp_git_repo)
    found = find_worktree_by_branch("feature/new", worktrees)
    assert found is not None


def test_create_worktree_existing_branch(
    temp_git_repo: git.Repo, change_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test creating worktree for existing branch."""
    os.chdir(temp_git_repo.working_dir)

    # Mock Confirm.ask
    from rich.prompt import Confirm

    monkeypatch.setattr(Confirm, "ask", lambda *args, **kwargs: True)

    # Create a branch first
    temp_git_repo.git.checkout("-b", "existing-branch")
    temp_git_repo.git.checkout("master")

    config = Config(
        worktree_dir=".worktrees/{branch}",
        hooks={"post_create": [], "pre_switch": [], "post_delete": []},
        settings=Settings(confirm_delete=False),
    )

    # Create worktree for existing branch
    worktree_path = create_worktree("existing-branch", skip_hooks=True, config=config)

    assert worktree_path.exists()
    assert "existing-branch" in str(worktree_path)


def test_create_worktree_custom_path(
    temp_git_repo: git.Repo, change_dir: Path, temp_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test creating worktree with custom path."""
    os.chdir(temp_git_repo.working_dir)

    # Mock Confirm.ask
    from rich.prompt import Confirm

    monkeypatch.setattr(Confirm, "ask", lambda *args, **kwargs: True)

    config = Config(
        hooks={"post_create": [], "pre_switch": [], "post_delete": []},
        settings=Settings(confirm_delete=False),
    )

    custom_path = str(temp_dir / "custom-worktree")

    # Create worktree with custom path
    worktree_path = create_worktree(
        "custom-branch", custom_path=custom_path, skip_hooks=True, config=config
    )

    # Use resolve() to handle symlinks on macOS
    assert worktree_path.resolve() == Path(custom_path).resolve()
    assert worktree_path.exists()
