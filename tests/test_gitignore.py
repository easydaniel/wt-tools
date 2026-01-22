"""Tests for gitignore management."""

import os
from pathlib import Path

import git
import pytest

from wt_tools.gitignore import (
    add_to_gitignore,
    check_gitignore_exists,
    create_gitignore,
    get_git_root,
    get_gitignore_path,
    is_pattern_ignored,
    read_gitignore,
)


def test_get_git_root(temp_git_repo: git.Repo, change_dir: Path) -> None:
    """Test finding git root directory."""
    os.chdir(temp_git_repo.working_dir)
    root = get_git_root()
    assert root == Path(temp_git_repo.working_dir)

    # Test from subdirectory
    subdir = Path(temp_git_repo.working_dir) / "subdir"
    subdir.mkdir()
    os.chdir(subdir)
    root = get_git_root()
    assert root == Path(temp_git_repo.working_dir)


def test_get_git_root_not_in_repo(temp_dir: Path, change_dir: Path) -> None:
    """Test get_git_root when not in a git repository."""
    os.chdir(temp_dir)
    root = get_git_root()
    assert root is None


def test_get_gitignore_path(temp_git_repo: git.Repo, change_dir: Path) -> None:
    """Test getting .gitignore path."""
    os.chdir(temp_git_repo.working_dir)
    gitignore_path = get_gitignore_path()
    assert gitignore_path == Path(temp_git_repo.working_dir) / ".gitignore"


def test_check_gitignore_exists(temp_git_repo: git.Repo, change_dir: Path) -> None:
    """Test checking if .gitignore exists."""
    os.chdir(temp_git_repo.working_dir)

    # Initially doesn't exist
    assert not check_gitignore_exists()

    # Create it
    gitignore = Path(temp_git_repo.working_dir) / ".gitignore"
    gitignore.write_text("*.pyc\n")

    # Now it exists
    assert check_gitignore_exists()


def test_read_gitignore(temp_git_repo: git.Repo, change_dir: Path) -> None:
    """Test reading .gitignore content."""
    os.chdir(temp_git_repo.working_dir)

    # No .gitignore
    lines = read_gitignore()
    assert lines == []

    # Create .gitignore
    gitignore = Path(temp_git_repo.working_dir) / ".gitignore"
    gitignore.write_text("*.pyc\n__pycache__/\n")

    lines = read_gitignore()
    assert len(lines) == 2
    assert "*.pyc\n" in lines
    assert "__pycache__/\n" in lines


def test_is_pattern_ignored(temp_git_repo: git.Repo, change_dir: Path) -> None:
    """Test checking if pattern is in .gitignore."""
    os.chdir(temp_git_repo.working_dir)

    # No .gitignore
    assert not is_pattern_ignored(".worktrees/")

    # Create .gitignore with patterns
    gitignore = Path(temp_git_repo.working_dir) / ".gitignore"
    gitignore.write_text("# Python\n*.pyc\n\n# Project\n.worktrees/\n")

    # Check patterns
    assert is_pattern_ignored(".worktrees/")
    assert is_pattern_ignored("*.pyc")
    assert not is_pattern_ignored(".venv/")

    # Comments and empty lines should be ignored
    assert not is_pattern_ignored("# Python")


def test_add_to_gitignore(temp_git_repo: git.Repo, change_dir: Path) -> None:
    """Test adding patterns to .gitignore."""
    os.chdir(temp_git_repo.working_dir)
    gitignore = Path(temp_git_repo.working_dir) / ".gitignore"

    # Create initial .gitignore
    gitignore.write_text("*.pyc\n")

    # Add new patterns
    success = add_to_gitignore([".worktrees/", ".wt-tools.yaml"], "wt-tools")
    assert success

    # Check content
    content = gitignore.read_text()
    assert "# wt-tools" in content
    assert ".worktrees/" in content
    assert ".wt-tools.yaml" in content
    assert "*.pyc" in content  # Original content preserved

    # Try adding existing pattern
    success = add_to_gitignore([".worktrees/"], "test")
    assert success  # Should succeed but not duplicate


def test_add_to_gitignore_no_newline(temp_git_repo: git.Repo, change_dir: Path) -> None:
    """Test adding to .gitignore that doesn't end with newline."""
    os.chdir(temp_git_repo.working_dir)
    gitignore = Path(temp_git_repo.working_dir) / ".gitignore"

    # Create .gitignore without trailing newline
    gitignore.write_text("*.pyc")

    success = add_to_gitignore([".worktrees/"])
    assert success

    content = gitignore.read_text()
    lines = content.split("\n")
    # Should have added empty line before new pattern
    assert len([line for line in lines if line.strip()]) >= 2


def test_create_gitignore(temp_git_repo: git.Repo, change_dir: Path) -> None:
    """Test creating new .gitignore file."""
    os.chdir(temp_git_repo.working_dir)
    gitignore = Path(temp_git_repo.working_dir) / ".gitignore"

    # Create .gitignore with patterns
    success = create_gitignore([".worktrees/", ".wt-tools.yaml"], "wt-tools config")
    assert success
    assert gitignore.exists()

    # Check content
    content = gitignore.read_text()
    assert "# wt-tools config" in content
    assert ".worktrees/" in content
    assert ".wt-tools.yaml" in content


def test_gitignore_not_in_repo(temp_dir: Path, change_dir: Path) -> None:
    """Test gitignore operations when not in a git repo."""
    os.chdir(temp_dir)

    # Should return None/False/[] gracefully
    assert get_gitignore_path() is None
    assert not check_gitignore_exists()
    assert read_gitignore() == []
    assert not is_pattern_ignored(".worktrees/")
    assert not add_to_gitignore([".worktrees/"])
    assert not create_gitignore([".worktrees/"])
