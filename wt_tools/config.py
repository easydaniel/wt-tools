"""Configuration management for wt-tools."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class HookConfig:
    """Configuration for a single hook."""

    name: str
    command: str
    working_dir: str = "{path}"
    timeout: int = 300
    env: Dict[str, str] = field(default_factory=dict)
    on_failure: str = "abort"  # abort, continue, warn

    def validate(self) -> None:
        """Validate hook configuration."""
        if not self.name:
            raise ValueError("Hook name cannot be empty")
        if not self.command:
            raise ValueError("Hook command cannot be empty")
        if self.on_failure not in ["abort", "continue", "warn"]:
            raise ValueError(f"Invalid on_failure value: {self.on_failure}")
        if self.timeout <= 0:
            raise ValueError("Hook timeout must be positive")


@dataclass
class Settings:
    """General settings for wt-tools."""

    auto_cleanup: bool = True
    confirm_delete: bool = True
    track_remote: bool = True


@dataclass
class Config:
    """Main configuration for wt-tools."""

    worktree_dir: str = ".worktrees/{branch}"
    worktree_dir_fallback: str = "~/.worktrees/{project}/{branch}"
    hooks: Dict[str, List[HookConfig]] = field(default_factory=dict)
    settings: Settings = field(default_factory=Settings)

    def __post_init__(self) -> None:
        """Initialize default hooks structure."""
        if not self.hooks:
            self.hooks = {
                "post_create": [],
                "pre_switch": [],
                "post_delete": [],
            }
        # Ensure settings is a Settings object
        if isinstance(self.settings, dict):
            self.settings = Settings(**self.settings)

    def validate(self) -> None:
        """Validate configuration."""
        if not self.worktree_dir:
            raise ValueError("worktree_dir cannot be empty")
        if not self.worktree_dir_fallback:
            raise ValueError("worktree_dir_fallback cannot be empty")

        # Validate all hooks
        for hook_type, hook_list in self.hooks.items():
            if hook_type not in ["post_create", "pre_switch", "post_delete"]:
                raise ValueError(f"Unknown hook type: {hook_type}")
            for hook in hook_list:
                hook.validate()


def get_global_config_path() -> Path:
    """Get path to global config file."""
    config_dir = Path.home() / ".config" / "wt-tools"
    return config_dir / "config.yaml"


def get_project_config_path() -> Optional[Path]:
    """Get path to project config file if in a git repository."""
    # Find git root
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            config_path = current / ".wt-tools.yaml"
            if config_path.exists():
                return config_path
            return None
        current = current.parent
    return None


def load_yaml_config(path: Path) -> Dict[str, Any]:
    """Load YAML configuration from file."""
    if not path.exists():
        return {}

    with open(path, "r") as f:
        data = yaml.safe_load(f)
        return data if data else {}


def parse_hooks(hooks_data: Dict[str, Any]) -> Dict[str, List[HookConfig]]:
    """Parse hooks from configuration data."""
    hooks: Dict[str, List[HookConfig]] = {
        "post_create": [],
        "pre_switch": [],
        "post_delete": [],
    }

    for hook_type, hook_list in hooks_data.items():
        if hook_type not in hooks:
            continue
        if not hook_list:
            continue

        for hook_data in hook_list:
            if isinstance(hook_data, dict):
                hook = HookConfig(
                    name=hook_data.get("name", ""),
                    command=hook_data.get("command", ""),
                    working_dir=hook_data.get("working_dir", "{path}"),
                    timeout=hook_data.get("timeout", 300),
                    env=hook_data.get("env", {}),
                    on_failure=hook_data.get("on_failure", "abort"),
                )
                hooks[hook_type].append(hook)

    return hooks


def load_global_config() -> Config:
    """Load global configuration."""
    config_path = get_global_config_path()
    data = load_yaml_config(config_path)

    hooks = parse_hooks(data.get("hooks", {}))
    settings_data = data.get("settings", {})

    return Config(
        worktree_dir=data.get("worktree_dir", ".worktrees/{branch}"),
        worktree_dir_fallback=data.get(
            "worktree_dir_fallback", "~/.worktrees/{project}/{branch}"
        ),
        hooks=hooks,
        settings=Settings(**settings_data) if settings_data else Settings(),
    )


def load_project_config() -> Optional[Config]:
    """Load project configuration if it exists."""
    config_path = get_project_config_path()
    if not config_path:
        return None

    data = load_yaml_config(config_path)
    hooks = parse_hooks(data.get("hooks", {}))
    settings_data = data.get("settings", {})

    return Config(
        worktree_dir=data.get("worktree_dir", ".worktrees/{branch}"),
        worktree_dir_fallback=data.get(
            "worktree_dir_fallback", "~/.worktrees/{project}/{branch}"
        ),
        hooks=hooks,
        settings=Settings(**settings_data) if settings_data else Settings(),
    )


def merge_configs(global_config: Config, project_config: Optional[Config]) -> Config:
    """Merge global and project configurations.

    Project config takes precedence for worktree_dir and settings.
    Hooks are concatenated (global first, then project).
    """
    if not project_config:
        return global_config

    # Use project config values, fallback to global
    worktree_dir = project_config.worktree_dir or global_config.worktree_dir
    worktree_dir_fallback = (
        project_config.worktree_dir_fallback or global_config.worktree_dir_fallback
    )

    # Merge hooks - concatenate lists
    merged_hooks: Dict[str, List[HookConfig]] = {
        "post_create": [],
        "pre_switch": [],
        "post_delete": [],
    }

    for hook_type in merged_hooks.keys():
        # Add global hooks first
        merged_hooks[hook_type].extend(global_config.hooks.get(hook_type, []))
        # Then add project hooks
        merged_hooks[hook_type].extend(project_config.hooks.get(hook_type, []))

    # Project settings override global settings
    # Create new Settings with project values, fallback to global
    merged_settings = Settings(
        auto_cleanup=project_config.settings.auto_cleanup
        if hasattr(project_config.settings, "auto_cleanup")
        else global_config.settings.auto_cleanup,
        confirm_delete=project_config.settings.confirm_delete
        if hasattr(project_config.settings, "confirm_delete")
        else global_config.settings.confirm_delete,
        track_remote=project_config.settings.track_remote
        if hasattr(project_config.settings, "track_remote")
        else global_config.settings.track_remote,
    )

    return Config(
        worktree_dir=worktree_dir,
        worktree_dir_fallback=worktree_dir_fallback,
        hooks=merged_hooks,
        settings=merged_settings,
    )


def load_config() -> Config:
    """Load and merge global and project configurations."""
    global_config = load_global_config()
    project_config = load_project_config()
    config = merge_configs(global_config, project_config)
    config.validate()
    return config


def substitute_variables(template: str, context: Dict[str, str]) -> str:
    """Substitute variables in a template string.

    Supported variables:
    - {branch}: Branch name
    - {path}: Worktree path
    - {project}: Project name
    - {date}: Current date (YYYY-MM-DD)
    - {short_hash}: Short git hash (first 7 chars)
    """
    result = template
    for key, value in context.items():
        result = result.replace(f"{{{key}}}", value)
    return result


def create_default_config() -> str:
    """Create default configuration YAML content."""
    return """# wt-tools configuration

# Directory pattern for worktrees
# Variables: {branch}, {project}, {date}, {short_hash}
worktree_dir: ".worktrees/{branch}"
worktree_dir_fallback: "~/.worktrees/{project}/{branch}"

# Hooks - custom scripts to run at different lifecycle events
hooks:
  # Run after creating a new worktree
  post_create: []
    # Example:
    # - name: "Install dependencies"
    #   command: "pip install -r requirements.txt"
    #   working_dir: "{path}"
    #   timeout: 300
    #   on_failure: "warn"  # abort, continue, or warn

  # Run before switching to a different worktree
  pre_switch: []
    # Example:
    # - name: "Auto-commit WIP"
    #   command: "git add -A && git commit -m 'WIP: auto-commit' || true"
    #   working_dir: "{path}"
    #   on_failure: "continue"

  # Run after deleting a worktree
  post_delete: []
    # Example:
    # - name: "Clean build artifacts"
    #   command: "rm -rf build/ dist/"
    #   working_dir: "{path}"
    #   on_failure: "warn"

# General settings
settings:
  auto_cleanup: true      # Automatically clean up stale worktrees
  confirm_delete: true    # Ask for confirmation before deleting
  track_remote: true      # Track remote branches when creating worktrees
"""


def save_config(config_path: Path, content: str) -> None:
    """Save configuration to file."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        f.write(content)
