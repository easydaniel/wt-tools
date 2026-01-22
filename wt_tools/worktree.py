"""Core worktree operations for wt-tools."""

import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import git
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

from .config import Config, load_config, substitute_variables
from .gitignore import ensure_patterns_ignored

console = Console()


@dataclass
class WorktreeInfo:
    """Information about a git worktree."""

    path: Path
    branch: str
    commit: str
    is_bare: bool = False
    is_detached: bool = False
    is_locked: bool = False


def get_repo() -> git.Repo:
    """Get the git repository for the current directory."""
    try:
        return git.Repo(Path.cwd(), search_parent_directories=True)
    except git.exc.InvalidGitRepositoryError:
        console.print("[red]Error: Not in a git repository[/red]")
        raise SystemExit(1)


def get_project_name(repo: git.Repo) -> str:
    """Get the project name from the repository."""
    repo_path = Path(repo.working_dir) if repo.working_dir else Path.cwd()
    return repo_path.name


def sanitize_branch_name(branch: str) -> str:
    """Sanitize branch name for use in directory names.

    Replaces slashes with hyphens and removes special characters.
    """
    return branch.replace("/", "-").replace("\\", "-")


def resolve_worktree_path(
    branch: str, config: Config, repo: git.Repo, use_fallback: bool = False
) -> Path:
    """Resolve the full path for a worktree.

    Args:
        branch: Branch name
        config: Configuration object
        repo: Git repository
        use_fallback: If True, use fallback path instead of primary

    Returns:
        Resolved Path for the worktree
    """
    # Get short hash
    try:
        short_hash = repo.head.commit.hexsha[:7]
    except Exception:
        short_hash = "0000000"

    # Build context for variable substitution
    context = {
        "branch": sanitize_branch_name(branch),
        "project": get_project_name(repo),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "short_hash": short_hash,
    }

    # Choose template
    template = config.worktree_dir_fallback if use_fallback else config.worktree_dir

    # Substitute variables
    path_str = substitute_variables(template, context)

    # Expand user directory
    path = Path(path_str).expanduser()

    # Make absolute if relative
    if not path.is_absolute():
        repo_root = Path(repo.working_dir) if repo.working_dir else Path.cwd()
        path = repo_root / path

    return path


def get_worktrees(repo: git.Repo) -> List[WorktreeInfo]:
    """Get list of all worktrees in the repository."""
    worktrees: List[WorktreeInfo] = []

    try:
        # Use git worktree list --porcelain for reliable parsing
        output = repo.git.worktree("list", "--porcelain")
        lines = output.strip().split("\n")

        current_wt: Dict[str, str] = {}
        for line in lines:
            if not line:
                # Empty line separates worktrees
                if current_wt:
                    worktrees.append(_parse_worktree_info(current_wt))
                    current_wt = {}
                continue

            if line.startswith("worktree "):
                current_wt["path"] = line[9:]
            elif line.startswith("HEAD "):
                current_wt["commit"] = line[5:]
            elif line.startswith("branch "):
                current_wt["branch"] = line[7:].replace("refs/heads/", "")
            elif line == "bare":
                current_wt["bare"] = "true"
            elif line == "detached":
                current_wt["detached"] = "true"
            elif line.startswith("locked"):
                current_wt["locked"] = "true"

        # Don't forget the last worktree
        if current_wt:
            worktrees.append(_parse_worktree_info(current_wt))

    except git.exc.GitCommandError as e:
        console.print(f"[red]Error listing worktrees: {e}[/red]")

    return worktrees


def _parse_worktree_info(data: Dict[str, str]) -> WorktreeInfo:
    """Parse worktree info from git worktree list output."""
    return WorktreeInfo(
        path=Path(data.get("path", "")),
        branch=data.get("branch", ""),
        commit=data.get("commit", "")[:7],
        is_bare=data.get("bare") == "true",
        is_detached=data.get("detached") == "true",
        is_locked=data.get("locked") == "true",
    )


def find_worktree_by_branch(branch: str, worktrees: List[WorktreeInfo]) -> Optional[WorktreeInfo]:
    """Find a worktree by branch name."""
    for wt in worktrees:
        if wt.branch == branch:
            return wt
    return None


def get_worktree_status(path: Path) -> str:
    """Get the status of a worktree (clean/modified)."""
    try:
        wt_repo = git.Repo(path)
        if wt_repo.is_dirty(untracked_files=True):
            return "modified"
        return "clean"
    except Exception:
        return "unknown"


def get_directory_size(path: Path) -> int:
    """Get the total size of a directory in bytes."""
    total = 0
    try:
        for entry in path.rglob("*"):
            if entry.is_file():
                total += entry.stat().st_size
    except (OSError, PermissionError):
        pass
    return total


def format_size(bytes_size: int) -> str:
    """Format size in bytes to human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


def create_worktree(
    branch: str,
    custom_path: Optional[str] = None,
    skip_hooks: bool = False,
    config: Optional[Config] = None,
) -> Path:
    """Create a new worktree.

    Args:
        branch: Branch name for the worktree
        custom_path: Optional custom path (overrides config)
        skip_hooks: Skip running post_create hooks
        config: Configuration (loaded if not provided)

    Returns:
        Path to the created worktree
    """
    if config is None:
        config = load_config()

    repo = get_repo()

    # Check if worktree already exists
    existing_worktrees = get_worktrees(repo)
    existing = find_worktree_by_branch(branch, existing_worktrees)
    if existing:
        console.print(f"[yellow]Worktree for branch '{branch}' already exists at {existing.path}[/yellow]")
        return existing.path

    # Determine worktree path
    if custom_path:
        worktree_path = Path(custom_path).expanduser().resolve()
    else:
        # Check if we need to update .gitignore
        worktree_path = resolve_worktree_path(branch, config, repo, use_fallback=False)

        # If using local .worktrees/, ensure it's in .gitignore
        if worktree_path.is_relative_to(repo.working_dir if repo.working_dir else Path.cwd()):
            patterns_added = ensure_patterns_ignored([".worktrees/"], "wt-tools worktree directories")
            if not patterns_added:
                # User declined gitignore update, use fallback
                console.print("[yellow]Using fallback worktree location[/yellow]")
                worktree_path = resolve_worktree_path(branch, config, repo, use_fallback=True)

    # Create parent directory if needed
    worktree_path.parent.mkdir(parents=True, exist_ok=True)

    # Create worktree
    try:
        console.print(f"[cyan]Creating worktree for '{branch}' at {worktree_path}[/cyan]")

        # Check if branch exists
        branch_exists = branch in [ref.name for ref in repo.references]

        if branch_exists:
            repo.git.worktree("add", str(worktree_path), branch)
        else:
            # Create new branch
            repo.git.worktree("add", "-b", branch, str(worktree_path))

        console.print(f"[green]✓ Worktree created at {worktree_path}[/green]")

    except git.exc.GitCommandError as e:
        console.print(f"[red]Error creating worktree: {e}[/red]")
        raise SystemExit(1)

    # Run post_create hooks
    if not skip_hooks and config.hooks.get("post_create"):
        from .hooks import execute_hooks

        context = {
            "branch": branch,
            "path": str(worktree_path),
            "project": get_project_name(repo),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "short_hash": repo.head.commit.hexsha[:7],
        }

        execute_hooks("post_create", config.hooks["post_create"], context)

    return worktree_path


def list_worktrees(verbose: bool = False) -> None:
    """List all worktrees.

    Args:
        verbose: Show additional information (status, size)
    """
    repo = get_repo()
    worktrees = get_worktrees(repo)

    if not worktrees:
        console.print("[yellow]No worktrees found[/yellow]")
        return

    # Get current worktree
    current_path = Path.cwd()

    # Create table
    table = Table(title="Git Worktrees")
    table.add_column("Branch", style="cyan")
    table.add_column("Path", style="white")
    table.add_column("Commit", style="yellow")

    if verbose:
        table.add_column("Status", style="green")
        table.add_column("Size", style="magenta")

    for wt in worktrees:
        # Skip bare repository
        if wt.is_bare:
            continue

        # Mark current worktree
        branch_display = wt.branch if wt.branch else "(detached)"
        if wt.path == current_path or (current_path.is_relative_to(wt.path) if wt.path.exists() else False):
            branch_display = f"* {branch_display}"

        row = [branch_display, str(wt.path), wt.commit]

        if verbose:
            status = get_worktree_status(wt.path)
            size = format_size(get_directory_size(wt.path))
            row.extend([status, size])

        table.add_row(*row)

    console.print(table)


def delete_worktree(
    branch: str,
    force: bool = False,
    keep_branch: bool = False,
    config: Optional[Config] = None,
) -> None:
    """Delete a worktree.

    Args:
        branch: Branch name of the worktree to delete
        force: Force deletion even if worktree is dirty
        keep_branch: Don't delete the branch, only the worktree
        config: Configuration (loaded if not provided)
    """
    if config is None:
        config = load_config()

    repo = get_repo()
    worktrees = get_worktrees(repo)

    # Find worktree
    worktree = find_worktree_by_branch(branch, worktrees)
    if not worktree:
        console.print(f"[red]No worktree found for branch '{branch}'[/red]")
        raise SystemExit(1)

    # Check if it's the main worktree
    repo_root = Path(repo.working_dir) if repo.working_dir else Path.cwd()
    if worktree.path == repo_root:
        console.print("[red]Cannot delete the main worktree[/red]")
        raise SystemExit(1)

    # Check for uncommitted changes
    if not force:
        status = get_worktree_status(worktree.path)
        if status == "modified":
            console.print(f"[yellow]Worktree has uncommitted changes[/yellow]")
            if not Confirm.ask("Delete anyway?"):
                console.print("[yellow]Deletion cancelled[/yellow]")
                return

    # Confirm deletion if configured
    if config.settings.confirm_delete and not force:
        if not Confirm.ask(f"Delete worktree for '{branch}' at {worktree.path}?"):
            console.print("[yellow]Deletion cancelled[/yellow]")
            return

    # Run pre_delete hooks
    if config.hooks.get("post_delete"):
        from .hooks import execute_hooks

        context = {
            "branch": branch,
            "path": str(worktree.path),
            "project": get_project_name(repo),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "short_hash": worktree.commit,
        }

        execute_hooks("post_delete", config.hooks["post_delete"], context)

    # Delete worktree
    try:
        console.print(f"[cyan]Deleting worktree at {worktree.path}[/cyan]")

        args = ["remove", str(worktree.path)]
        if force:
            args.append("--force")

        repo.git.worktree(*args)
        console.print(f"[green]✓ Worktree deleted[/green]")

        # Delete branch if requested
        if not keep_branch:
            try:
                repo.git.branch("-D", branch)
                console.print(f"[green]✓ Branch '{branch}' deleted[/green]")
            except git.exc.GitCommandError as e:
                console.print(f"[yellow]Warning: Could not delete branch: {e}[/yellow]")

    except git.exc.GitCommandError as e:
        console.print(f"[red]Error deleting worktree: {e}[/red]")
        raise SystemExit(1)


def cleanup_worktrees(dry_run: bool = False) -> None:
    """Clean up stale worktrees.

    Args:
        dry_run: Show what would be cleaned up without actually doing it
    """
    repo = get_repo()

    try:
        # Run git worktree prune in dry-run mode first
        console.print("[cyan]Checking for stale worktrees...[/cyan]")

        if dry_run:
            console.print("[yellow]Dry run - no changes will be made[/yellow]")
            # List worktrees that would be pruned
            output = repo.git.worktree("prune", "--dry-run", "--verbose")
            if output:
                console.print(output)
            else:
                console.print("[green]No stale worktrees found[/green]")
        else:
            # Actually prune
            repo.git.worktree("prune", "--verbose")
            console.print("[green]✓ Cleaned up stale worktrees[/green]")

    except git.exc.GitCommandError as e:
        console.print(f"[red]Error during cleanup: {e}[/red]")
        raise SystemExit(1)


def switch_worktree(branch: str) -> Path:
    """Switch to a worktree.

    This doesn't actually change directories (that's a shell operation),
    but returns the path that should be cd'd to.

    Args:
        branch: Branch name of the worktree to switch to

    Returns:
        Path to the worktree
    """
    repo = get_repo()
    worktrees = get_worktrees(repo)

    # Find worktree
    worktree = find_worktree_by_branch(branch, worktrees)
    if not worktree:
        console.print(f"[red]No worktree found for branch '{branch}'[/red]")
        raise SystemExit(1)

    # Run pre_switch hooks on current worktree
    config = load_config()
    if config.hooks.get("pre_switch"):
        from .hooks import execute_hooks

        current_path = Path.cwd()
        context = {
            "branch": branch,
            "path": str(current_path),
            "project": get_project_name(repo),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "short_hash": repo.head.commit.hexsha[:7],
        }

        execute_hooks("pre_switch", config.hooks["pre_switch"], context)

    return worktree.path
