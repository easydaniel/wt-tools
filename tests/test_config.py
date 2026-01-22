"""Tests for configuration management."""

from pathlib import Path

import pytest
import yaml

from wt_tools.config import (
    Config,
    HookConfig,
    Settings,
    create_default_config,
    load_config,
    load_global_config,
    load_yaml_config,
    merge_configs,
    parse_hooks,
    save_config,
    substitute_variables,
)


def test_hook_config_validation() -> None:
    """Test HookConfig validation."""
    # Valid hook
    hook = HookConfig(name="Test", command="echo test")
    hook.validate()  # Should not raise

    # Invalid: empty name
    with pytest.raises(ValueError, match="name cannot be empty"):
        hook = HookConfig(name="", command="echo test")
        hook.validate()

    # Invalid: empty command
    with pytest.raises(ValueError, match="command cannot be empty"):
        hook = HookConfig(name="Test", command="")
        hook.validate()

    # Invalid: bad on_failure
    with pytest.raises(ValueError, match="Invalid on_failure"):
        hook = HookConfig(name="Test", command="echo test", on_failure="invalid")
        hook.validate()

    # Invalid: negative timeout
    with pytest.raises(ValueError, match="timeout must be positive"):
        hook = HookConfig(name="Test", command="echo test", timeout=-1)
        hook.validate()


def test_config_initialization() -> None:
    """Test Config initialization."""
    config = Config()

    assert config.worktree_dir == ".worktrees/{branch}"
    assert config.worktree_dir_fallback == "~/.worktrees/{project}/{branch}"
    assert "post_create" in config.hooks
    assert "pre_switch" in config.hooks
    assert "post_delete" in config.hooks
    assert isinstance(config.settings, Settings)


def test_config_validation() -> None:
    """Test Config validation."""
    # Valid config
    config = Config()
    config.validate()  # Should not raise

    # Invalid: empty worktree_dir
    with pytest.raises(ValueError, match="worktree_dir cannot be empty"):
        config = Config(worktree_dir="")
        config.validate()


def test_load_yaml_config(temp_dir: Path, sample_config_yaml: str) -> None:
    """Test loading YAML configuration."""
    # Non-existent file
    result = load_yaml_config(temp_dir / "nonexistent.yaml")
    assert result == {}

    # Valid file
    config_file = temp_dir / "config.yaml"
    config_file.write_text(sample_config_yaml)
    result = load_yaml_config(config_file)

    assert result["worktree_dir"] == ".worktrees/{branch}"
    assert "hooks" in result
    assert "post_create" in result["hooks"]


def test_parse_hooks() -> None:
    """Test parsing hooks from configuration data."""
    hooks_data = {
        "post_create": [
            {
                "name": "Install deps",
                "command": "pip install -r requirements.txt",
                "working_dir": "{path}",
                "timeout": 600,
                "on_failure": "abort",
            }
        ],
        "pre_switch": [],
        "post_delete": [
            {"name": "Clean", "command": "rm -rf build/", "on_failure": "warn"}
        ],
    }

    hooks = parse_hooks(hooks_data)

    assert len(hooks["post_create"]) == 1
    assert hooks["post_create"][0].name == "Install deps"
    assert hooks["post_create"][0].timeout == 600

    assert len(hooks["pre_switch"]) == 0

    assert len(hooks["post_delete"]) == 1
    assert hooks["post_delete"][0].on_failure == "warn"


def test_merge_configs() -> None:
    """Test merging global and project configurations."""
    global_config = Config(
        worktree_dir=".worktrees/{branch}",
        hooks={
            "post_create": [HookConfig(name="Global hook", command="echo global")],
            "pre_switch": [],
            "post_delete": [],
        },
        settings=Settings(auto_cleanup=True, confirm_delete=True),
    )

    project_config = Config(
        worktree_dir=".my-worktrees/{branch}",
        hooks={
            "post_create": [HookConfig(name="Project hook", command="echo project")],
            "pre_switch": [],
            "post_delete": [],
        },
        settings=Settings(auto_cleanup=False),
    )

    merged = merge_configs(global_config, project_config)

    # Project config should override worktree_dir
    assert merged.worktree_dir == ".my-worktrees/{branch}"

    # Hooks should be concatenated
    assert len(merged.hooks["post_create"]) == 2
    assert merged.hooks["post_create"][0].name == "Global hook"
    assert merged.hooks["post_create"][1].name == "Project hook"

    # Settings should use project values
    assert merged.settings.auto_cleanup is False
    assert merged.settings.confirm_delete is True


def test_merge_configs_no_project() -> None:
    """Test merging when project config is None."""
    global_config = Config()
    merged = merge_configs(global_config, None)

    assert merged.worktree_dir == global_config.worktree_dir
    assert merged.hooks == global_config.hooks


def test_substitute_variables() -> None:
    """Test variable substitution."""
    template = "Path: {path}, Branch: {branch}, Project: {project}"
    context = {"path": "/tmp/worktree", "branch": "feature/test", "project": "myapp"}

    result = substitute_variables(template, context)
    assert result == "Path: /tmp/worktree, Branch: feature/test, Project: myapp"

    # With missing variables
    template_with_missing = "{path} {missing}"
    result = substitute_variables(template_with_missing, context)
    assert result == "/tmp/worktree {missing}"


def test_create_default_config() -> None:
    """Test creating default configuration."""
    config_content = create_default_config()

    assert "worktree_dir:" in config_content
    assert "hooks:" in config_content
    assert "post_create:" in config_content
    assert "settings:" in config_content

    # Should be valid YAML
    data = yaml.safe_load(config_content)
    assert "worktree_dir" in data
    assert "hooks" in data


def test_save_config(temp_dir: Path) -> None:
    """Test saving configuration to file."""
    config_path = temp_dir / "test-config.yaml"
    content = "test: value\n"

    save_config(config_path, content)

    assert config_path.exists()
    assert config_path.read_text() == content

    # Test with nested directory
    nested_path = temp_dir / "nested" / "dir" / "config.yaml"
    save_config(nested_path, content)

    assert nested_path.exists()
    assert nested_path.read_text() == content
