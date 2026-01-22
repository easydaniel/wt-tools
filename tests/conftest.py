"""Pytest fixtures for wt-tools tests."""

import os
import tempfile
from pathlib import Path
from typing import Generator

import git
import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_git_repo(temp_dir: Path) -> git.Repo:
    """Create a temporary git repository."""
    repo = git.Repo.init(temp_dir)

    # Configure git user for commits
    repo.config_writer().set_value("user", "name", "Test User").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()

    # Create initial commit
    readme = temp_dir / "README.md"
    readme.write_text("# Test Repository\n")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    return repo


@pytest.fixture
def config_dir(temp_dir: Path) -> Path:
    """Create a temporary config directory."""
    config_path = temp_dir / ".config" / "wt-tools"
    config_path.mkdir(parents=True)
    return config_path


@pytest.fixture
def sample_config_yaml() -> str:
    """Sample configuration YAML content."""
    return """
worktree_dir: ".worktrees/{branch}"
worktree_dir_fallback: "~/.worktrees/{project}/{branch}"

hooks:
  post_create:
    - name: "Test hook"
      command: "echo 'Hello'"
      working_dir: "{path}"
      timeout: 300
      on_failure: "warn"

  pre_switch: []
  post_delete: []

settings:
  auto_cleanup: true
  confirm_delete: true
  track_remote: true
"""


@pytest.fixture
def change_dir(temp_dir: Path) -> Generator[Path, None, None]:
    """Change to temporary directory and restore original directory after test."""
    original_dir = Path.cwd()
    os.chdir(temp_dir)
    yield temp_dir
    os.chdir(original_dir)
