"""Gitignore management utilities for wt-tools."""

from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.prompt import Confirm

console = Console()


def get_git_root() -> Optional[Path]:
    """Find the root directory of the git repository."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return None


def get_gitignore_path() -> Optional[Path]:
    """Get path to .gitignore file in repository root."""
    git_root = get_git_root()
    if not git_root:
        return None
    return git_root / ".gitignore"


def check_gitignore_exists() -> bool:
    """Check if .gitignore file exists in repository root."""
    gitignore_path = get_gitignore_path()
    return gitignore_path is not None and gitignore_path.exists()


def read_gitignore() -> List[str]:
    """Read lines from .gitignore file."""
    gitignore_path = get_gitignore_path()
    if not gitignore_path or not gitignore_path.exists():
        return []

    with open(gitignore_path, "r") as f:
        return f.readlines()


def is_pattern_ignored(pattern: str) -> bool:
    """Check if a pattern is already in .gitignore.

    Args:
        pattern: The gitignore pattern to check (e.g., ".worktrees/")

    Returns:
        True if pattern is already in .gitignore
    """
    lines = read_gitignore()
    pattern_stripped = pattern.strip()

    for line in lines:
        line_stripped = line.strip()
        # Skip comments and empty lines
        if not line_stripped or line_stripped.startswith("#"):
            continue
        if line_stripped == pattern_stripped:
            return True

    return False


def add_to_gitignore(patterns: List[str], comment: Optional[str] = None) -> bool:
    """Add patterns to .gitignore file.

    Args:
        patterns: List of gitignore patterns to add
        comment: Optional comment to add before the patterns

    Returns:
        True if successful, False otherwise
    """
    gitignore_path = get_gitignore_path()
    if not gitignore_path:
        console.print("[yellow]Warning: Not in a git repository[/yellow]")
        return False

    try:
        # Read existing content
        existing_content = ""
        if gitignore_path.exists():
            with open(gitignore_path, "r") as f:
                existing_content = f.read()

        # Prepare new content
        lines_to_add = []

        # Add a newline if file doesn't end with one
        if existing_content and not existing_content.endswith("\n"):
            lines_to_add.append("")

        # Add comment if provided
        if comment:
            lines_to_add.append(f"# {comment}")

        # Add patterns
        for pattern in patterns:
            if not is_pattern_ignored(pattern):
                lines_to_add.append(pattern)

        # Write to file
        if lines_to_add:
            with open(gitignore_path, "a") as f:
                f.write("\n".join(lines_to_add) + "\n")
            return True

        return True  # Patterns already exist

    except (IOError, PermissionError) as e:
        console.print(f"[red]Error writing to .gitignore: {e}[/red]")
        return False


def create_gitignore(patterns: List[str], comment: Optional[str] = None) -> bool:
    """Create a new .gitignore file with the given patterns.

    Args:
        patterns: List of gitignore patterns to add
        comment: Optional comment to add before the patterns

    Returns:
        True if successful, False otherwise
    """
    gitignore_path = get_gitignore_path()
    if not gitignore_path:
        console.print("[yellow]Warning: Not in a git repository[/yellow]")
        return False

    try:
        lines = []

        # Add comment if provided
        if comment:
            lines.append(f"# {comment}")

        # Add patterns
        lines.extend(patterns)

        # Write to file
        with open(gitignore_path, "w") as f:
            f.write("\n".join(lines) + "\n")

        console.print(f"[green]Created .gitignore with {len(patterns)} pattern(s)[/green]")
        return True

    except (IOError, PermissionError) as e:
        console.print(f"[red]Error creating .gitignore: {e}[/red]")
        return False


def prompt_gitignore_update(
    patterns: List[str], reason: str = "wt-tools configuration"
) -> bool:
    """Prompt user to add patterns to .gitignore.

    Args:
        patterns: List of patterns to add
        reason: Reason for adding (shown in prompt)

    Returns:
        True if user accepted and patterns were added, False otherwise
    """
    # Check if .gitignore exists
    if not check_gitignore_exists():
        # Offer to create .gitignore
        should_create = Confirm.ask(
            f"[yellow].gitignore not found. Create it with {reason} patterns?[/yellow]"
        )
        if should_create:
            return create_gitignore(patterns, reason)
        return False

    # Check which patterns are not already ignored
    patterns_to_add = [p for p in patterns if not is_pattern_ignored(p)]

    if not patterns_to_add:
        # All patterns already in .gitignore
        return True

    # Show patterns and ask for confirmation
    console.print(f"\n[bold]Patterns to add to .gitignore:[/bold]")
    for pattern in patterns_to_add:
        console.print(f"  • {pattern}")
    console.print()

    should_add = Confirm.ask(
        f"[yellow]Add these patterns to .gitignore for {reason}?[/yellow]"
    )

    if should_add:
        success = add_to_gitignore(patterns_to_add, reason)
        if success:
            console.print(
                f"[green]Added {len(patterns_to_add)} pattern(s) to .gitignore[/green]"
            )
        return success

    return False


def ensure_patterns_ignored(
    patterns: List[str], reason: str = "wt-tools configuration"
) -> bool:
    """Ensure patterns are in .gitignore, prompting user if needed.

    This is a convenience function that combines checking and prompting.

    Args:
        patterns: List of patterns to ensure are ignored
        reason: Reason for adding (shown in prompt)

    Returns:
        True if all patterns are ignored (either already or newly added)
    """
    # Check if all patterns are already ignored
    all_ignored = all(is_pattern_ignored(p) for p in patterns)
    if all_ignored:
        return True

    # Prompt to add missing patterns
    return prompt_gitignore_update(patterns, reason)
