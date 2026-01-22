"""Hook execution engine for wt-tools."""

import os
import subprocess
import time
from typing import Dict, List

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import HookConfig, substitute_variables

console = Console()


class HookExecutionError(Exception):
    """Exception raised when a hook fails with abort mode."""

    pass


def execute_hooks(
    hook_type: str, hooks: List[HookConfig], context: Dict[str, str]
) -> None:
    """Execute a list of hooks of a specific type.

    Args:
        hook_type: Type of hook (post_create, pre_switch, post_delete)
        hooks: List of hook configurations to execute
        context: Context variables for substitution

    Raises:
        HookExecutionError: If a hook fails with on_failure='abort'
    """
    if not hooks:
        return

    console.print(f"\n[bold cyan]Running {hook_type} hooks...[/bold cyan]")

    for i, hook in enumerate(hooks, 1):
        console.print(f"\n[dim]Hook {i}/{len(hooks)}[/dim]")
        success = run_hook(hook, context)

        if not success:
            if hook.on_failure == "abort":
                console.print(f"[red]✗ Hook '{hook.name}' failed - aborting[/red]")
                raise HookExecutionError(f"Hook '{hook.name}' failed")
            elif hook.on_failure == "warn":
                console.print(
                    f"[yellow]⚠ Hook '{hook.name}' failed - continuing with warning[/yellow]"
                )
            # 'continue' mode just continues without special message

    console.print(f"\n[green]✓ All {hook_type} hooks completed[/green]")


def run_hook(hook: HookConfig, context: Dict[str, str]) -> bool:
    """Run a single hook.

    Args:
        hook: Hook configuration
        context: Context variables for substitution

    Returns:
        True if hook succeeded, False otherwise
    """
    # Substitute variables in command
    command = substitute_variables(hook.command, context)
    working_dir = substitute_variables(hook.working_dir, context)

    # Prepare environment
    env = os.environ.copy()
    for key, value in hook.env.items():
        env[key] = substitute_variables(value, context)

    # Display hook info
    console.print(f"[bold]{hook.name}[/bold]")
    console.print(f"[dim]Command: {command}[/dim]")
    console.print(f"[dim]Working dir: {working_dir}[/dim]")

    # Execute with spinner
    start_time = time.time()

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"Running {hook.name}...", total=None)

            # Run command
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                env=env,
                timeout=hook.timeout,
                capture_output=True,
                text=True,
            )

            progress.update(task, completed=True)

        elapsed = time.time() - start_time

        # Check result
        if result.returncode == 0:
            console.print(f"[green]✓ {hook.name}[/green] [dim]({elapsed:.1f}s)[/dim]")

            # Show output if verbose or if there's important info
            if result.stdout and result.stdout.strip():
                console.print(f"[dim]{result.stdout.strip()}[/dim]")

            return True
        else:
            console.print(
                f"[red]✗ {hook.name}[/red] [dim]({elapsed:.1f}s)[/dim]"
            )
            console.print(f"[red]Exit code: {result.returncode}[/red]")

            # Show error output
            if result.stderr:
                console.print(f"[red]Error output:[/red]\n{result.stderr.strip()}")
            elif result.stdout:
                console.print(f"[yellow]Output:[/yellow]\n{result.stdout.strip()}")

            return False

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        console.print(
            f"[red]✗ {hook.name}[/red] [dim]({elapsed:.1f}s)[/dim]"
        )
        console.print(f"[red]Timeout: Hook exceeded {hook.timeout}s limit[/red]")
        return False

    except FileNotFoundError:
        elapsed = time.time() - start_time
        console.print(
            f"[red]✗ {hook.name}[/red] [dim]({elapsed:.1f}s)[/dim]"
        )
        console.print(f"[red]Error: Working directory not found: {working_dir}[/red]")
        return False

    except Exception as e:
        elapsed = time.time() - start_time
        console.print(
            f"[red]✗ {hook.name}[/red] [dim]({elapsed:.1f}s)[/dim]"
        )
        console.print(f"[red]Unexpected error: {e}[/red]")
        return False
