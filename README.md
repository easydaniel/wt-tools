# wt-tools

[![PyPI version](https://badge.fury.io/py/wt-tools.svg)](https://badge.fury.io/py/wt-tools)
[![Tests](https://github.com/easydaniel/wt-tools/actions/workflows/test.yml/badge.svg)](https://github.com/easydaniel/wt-tools/actions/workflows/test.yml)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Git worktree management with configurable hooks.

## Features

- **Easy Worktree Management**: Create, list, delete, and switch between git worktrees
- **Configurable Hooks**: Run custom scripts on post_create, pre_switch, and post_delete events
- **Smart Configuration**: Global and project-level config files with intelligent merging
- **Automatic Gitignore**: Prompts to add worktree directories to .gitignore with fallback strategies
- **Beautiful CLI**: Rich terminal output with progress indicators and formatting

## Installation

```bash
pip install wt-tools
```

## Quick Start

### Option 1: Existing Repository

1. Initialize wt-tools in your git repository:

```bash
cd /path/to/your/repo
wt init
```

### Option 2: Clone New Repository

Clone a repository with wt-tools already configured:

```bash
wt clone https://github.com/user/repo.git
cd repo
```

### Working with Worktrees

1. Create a new worktree:

```bash
wt create feature/new-feature
```

3. List all worktrees:

```bash
wt list
```

4. Switch to a worktree:

```bash
cd $(wt switch feature/new-feature)
```

5. Delete a worktree:

```bash
wt delete feature/new-feature
```

## Configuration

wt-tools uses two levels of configuration:

- **Global config**: `~/.config/wt-tools/config.yaml`
- **Project config**: `.wt-tools.yaml` (in your repository root)

Example `.wt-tools.yaml`:

```yaml
worktree_dir: ".worktrees/{branch}"
worktree_dir_fallback: "~/.worktrees/{project}/{branch}"

hooks:
  post_create:
    - name: "Install dependencies"
      command: "pip install -r requirements.txt"
      working_dir: "{path}"
      on_failure: "warn"

  pre_switch:
    - name: "Auto-commit WIP"
      command: "git add -A && git commit -m 'WIP: auto-commit' || true"
      working_dir: "{path}"
      on_failure: "continue"

settings:
  auto_cleanup: true
  confirm_delete: true
  track_remote: true
```

## Commands

- `wt init` - Initialize wt-tools configuration
- `wt create <branch>` - Create a new worktree
- `wt list` - List all worktrees
- `wt delete <branch>` - Delete a worktree
- `wt switch <branch>` - Switch to a worktree
- `wt cleanup` - Clean up stale worktrees
- `wt config` - Show current configuration

## Development

```bash
# Clone the repository
git clone https://github.com/easydaniel/wt-tools.git
cd wt-tools

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run type checking
mypy wt_tools

# Format code
black wt_tools tests
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
