"""CLI interface for wt-tools."""

import sys
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.syntax import Syntax

from . import __version__
from .config import (
    create_default_config,
    get_global_config_path,
    get_project_config_path,
    load_config,
    save_config,
)
from .gitignore import ensure_patterns_ignored
from .worktree import (
    cleanup_worktrees,
    create_worktree,
    delete_worktree,
    list_worktrees,
    switch_worktree,
)

console = Console()


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """Git worktree management with hooks.

    wt-tools helps you manage git worktrees with configurable hooks
    for automation and workflow customization.
    """
    pass


@cli.command()
@click.option(
    "--global",
    "global_",
    is_flag=True,
    help="Initialize global config instead of project config",
)
def init(global_: bool) -> None:
    """Initialize wt-tools configuration.

    Creates a default configuration file with example hooks.
    """
    if global_:
        # Initialize global config
        config_path = get_global_config_path()
        if config_path.exists():
            console.print(
                f"[yellow]Global config already exists at {config_path}[/yellow]"
            )
            if not click.confirm("Overwrite?"):
                console.print("[yellow]Initialization cancelled[/yellow]")
                return

        config_content = create_default_config()
        save_config(config_path, config_content)
        console.print(f"[green]✓ Created global config at {config_path}[/green]")

    else:
        # Initialize project config
        project_config_path = Path.cwd() / ".wt-tools.yaml"
        if project_config_path.exists():
            console.print(
                f"[yellow]Project config already exists at {project_config_path}[/yellow]"
            )
            if not click.confirm("Overwrite?"):
                console.print("[yellow]Initialization cancelled[/yellow]")
                return

        # Prompt to add to .gitignore
        patterns_added = ensure_patterns_ignored(
            [".worktrees/", ".wt-tools.yaml"], "wt-tools configuration"
        )

        config_content = create_default_config()
        save_config(project_config_path, config_content)
        console.print(
            f"[green]✓ Created project config at {project_config_path}[/green]"
        )

    console.print("\n[cyan]Edit the config file to customize hooks and settings.[/cyan]")


@cli.command()
@click.argument("branch")
@click.option("--path", help="Custom worktree path (overrides config)")
@click.option("--skip-hooks", is_flag=True, help="Skip running post_create hooks")
def create(branch: str, path: str, skip_hooks: bool) -> None:
    """Create a new worktree.

    Creates a new git worktree for the specified BRANCH.
    If the branch doesn't exist, it will be created.

    Examples:

        wt create feature/new-feature

        wt create bugfix/issue-123 --path /tmp/bugfix

        wt create experiment --skip-hooks
    """
    try:
        worktree_path = create_worktree(
            branch=branch, custom_path=path, skip_hooks=skip_hooks
        )
        console.print(f"\n[green]Worktree ready at: {worktree_path}[/green]")
        console.print(f"\n[cyan]To switch: cd {worktree_path}[/cyan]")
    except SystemExit:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command(name="list")
@click.option("--verbose", "-v", is_flag=True, help="Show additional information")
def list_cmd(verbose: bool) -> None:
    """List all worktrees.

    Shows all git worktrees with their branch, path, and commit.
    Use --verbose to see status and disk usage.

    Examples:

        wt list

        wt list --verbose
    """
    try:
        list_worktrees(verbose=verbose)
    except SystemExit:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("branch")
@click.option("--force", "-f", is_flag=True, help="Force deletion even if worktree is dirty")
@click.option("--keep-branch", is_flag=True, help="Keep the branch, only delete worktree")
def delete(branch: str, force: bool, keep_branch: bool) -> None:
    """Delete a worktree.

    Removes the worktree for the specified BRANCH.
    By default, also deletes the branch.

    Examples:

        wt delete feature/old-feature

        wt delete bugfix/issue-123 --keep-branch

        wt delete experiment --force
    """
    try:
        delete_worktree(branch=branch, force=force, keep_branch=keep_branch)
    except SystemExit:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("branch")
def switch(branch: str) -> None:
    """Switch to a worktree.

    Prints the path to the worktree for the specified BRANCH.
    Use with command substitution to change directory.

    Examples:

        cd $(wt switch feature/new-feature)

        # Or create an alias in your shell:
        alias wts='cd $(wt switch $1)'
    """
    try:
        worktree_path = switch_worktree(branch)
        # Print only the path for shell command substitution
        print(worktree_path)
    except SystemExit:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]", file=sys.stderr)
        sys.exit(1)


@cli.command()
@click.option(
    "--global",
    "global_",
    is_flag=True,
    help="Show global config",
)
@click.option(
    "--project",
    is_flag=True,
    help="Show project config",
)
def config(global_: bool, project: bool) -> None:
    """Show configuration.

    Displays the current configuration. By default, shows the merged config.
    Use --global or --project to show specific configs.

    Examples:

        wt config

        wt config --global

        wt config --project
    """
    try:
        if global_:
            config_path = get_global_config_path()
            if not config_path.exists():
                console.print("[yellow]No global config found[/yellow]")
                console.print(f"[cyan]Create one with: wt init --global[/cyan]")
                return

            console.print(f"[bold]Global config:[/bold] {config_path}\n")
            with open(config_path, "r") as f:
                content = f.read()

        elif project:
            config_path = get_project_config_path()
            if not config_path:
                console.print("[yellow]No project config found[/yellow]")
                console.print(f"[cyan]Create one with: wt init[/cyan]")
                return

            console.print(f"[bold]Project config:[/bold] {config_path}\n")
            with open(config_path, "r") as f:
                content = f.read()

        else:
            # Show merged config
            merged_config = load_config()
            console.print("[bold]Merged configuration:[/bold]\n")

            # Convert to YAML for display
            config_dict = {
                "worktree_dir": merged_config.worktree_dir,
                "worktree_dir_fallback": merged_config.worktree_dir_fallback,
                "hooks": {
                    "post_create": [
                        {
                            "name": h.name,
                            "command": h.command,
                            "working_dir": h.working_dir,
                            "timeout": h.timeout,
                            "on_failure": h.on_failure,
                        }
                        for h in merged_config.hooks.get("post_create", [])
                    ],
                    "pre_switch": [
                        {
                            "name": h.name,
                            "command": h.command,
                            "working_dir": h.working_dir,
                            "timeout": h.timeout,
                            "on_failure": h.on_failure,
                        }
                        for h in merged_config.hooks.get("pre_switch", [])
                    ],
                    "post_delete": [
                        {
                            "name": h.name,
                            "command": h.command,
                            "working_dir": h.working_dir,
                            "timeout": h.timeout,
                            "on_failure": h.on_failure,
                        }
                        for h in merged_config.hooks.get("post_delete", [])
                    ],
                },
                "settings": {
                    "auto_cleanup": merged_config.settings.auto_cleanup,
                    "confirm_delete": merged_config.settings.confirm_delete,
                    "track_remote": merged_config.settings.track_remote,
                },
            }
            content = yaml.dump(config_dict, default_flow_style=False, sort_keys=False)

        # Display with syntax highlighting
        syntax = Syntax(content, "yaml", theme="monokai", line_numbers=False)
        console.print(syntax)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--dry-run", is_flag=True, help="Show what would be cleaned up")
def cleanup(dry_run: bool) -> None:
    """Clean up stale worktrees.

    Removes worktree administrative files for worktrees that no longer exist.

    Examples:

        wt cleanup --dry-run

        wt cleanup
    """
    try:
        cleanup_worktrees(dry_run=dry_run)
    except SystemExit:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
