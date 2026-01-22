# Configuration Reference

wt-tools uses YAML configuration files to customize behavior and define hooks.

## Configuration Levels

wt-tools supports two levels of configuration:

1. **Global Configuration**: `~/.config/wt-tools/config.yaml`
   - Applies to all projects
   - Created with `wt init --global`

2. **Project Configuration**: `.wt-tools.yaml` (in repository root)
   - Applies to current project only
   - Created with `wt init`
   - Overrides global settings

### Configuration Merging

When both global and project configs exist, they are merged with the following rules:

- **worktree_dir** and **settings**: Project values override global values
- **hooks**: Lists are concatenated (global hooks run first, then project hooks)

## Configuration Structure

```yaml
# Directory pattern for worktrees
worktree_dir: ".worktrees/{branch}"
worktree_dir_fallback: "~/.worktrees/{project}/{branch}"

# Hooks for automation
hooks:
  post_create: []
  pre_switch: []
  post_delete: []

# General settings
settings:
  auto_cleanup: true
  confirm_delete: true
  track_remote: true
```

## Worktree Directory Configuration

### worktree_dir

Primary directory pattern for creating worktrees.

**Default**: `.worktrees/{branch}`

**Variables**:
- `{branch}`: Sanitized branch name (slashes replaced with hyphens)
- `{project}`: Project/repository name
- `{date}`: Current date (YYYY-MM-DD)
- `{short_hash}`: First 7 characters of current commit hash

**Examples**:
```yaml
# Relative to repo root
worktree_dir: ".worktrees/{branch}"

# Absolute path with project name
worktree_dir: "/tmp/worktrees/{project}/{branch}"

# With date for temporary worktrees
worktree_dir: ".worktrees/{date}-{branch}"
```

### worktree_dir_fallback

Fallback directory pattern used when user declines to add `.worktrees/` to `.gitignore`.

**Default**: `~/.worktrees/{project}/{branch}`

This prevents worktree directories from being accidentally committed.

## Hooks

Hooks are custom scripts that run automatically at specific lifecycle events.

### Hook Types

1. **post_create**: Runs after creating a new worktree
2. **pre_switch**: Runs before switching to a different worktree
3. **post_delete**: Runs after deleting a worktree

### Hook Configuration

Each hook is defined as:

```yaml
hooks:
  post_create:
    - name: "Descriptive name"
      command: "shell command to execute"
      working_dir: "{path}"
      timeout: 300
      env:
        VAR_NAME: "value"
      on_failure: "abort"
```

### Hook Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `name` | string | Required | Descriptive name shown during execution |
| `command` | string | Required | Shell command to execute |
| `working_dir` | string | `{path}` | Directory to run command in |
| `timeout` | integer | 300 | Timeout in seconds |
| `env` | object | `{}` | Environment variables to set |
| `on_failure` | string | `"abort"` | Failure mode: `abort`, `continue`, or `warn` |

### Failure Modes

- **abort**: Stop execution and exit with error
- **continue**: Show warning and continue to next hook
- **warn**: Show warning with details but continue

### Variable Substitution in Hooks

All string values in hooks support variable substitution:

- `{branch}`: Branch name
- `{path}`: Worktree path
- `{project}`: Project name
- `{date}`: Current date
- `{short_hash}`: Short commit hash

**Example**:
```yaml
hooks:
  post_create:
    - name: "Create log file"
      command: "echo 'Created on {date}' > {path}/worktree.log"
```

## Settings

### auto_cleanup

Automatically run cleanup when it detects stale worktrees.

**Type**: boolean
**Default**: `true`

### confirm_delete

Ask for confirmation before deleting worktrees.

**Type**: boolean
**Default**: `true`

Set to `false` to skip confirmation (useful for automation).

### track_remote

Automatically set up remote tracking for new branches in worktrees.

**Type**: boolean
**Default**: `true`

## Complete Example

```yaml
worktree_dir: ".worktrees/{branch}"
worktree_dir_fallback: "~/.worktrees/{project}/{branch}"

hooks:
  post_create:
    - name: "Install Python dependencies"
      command: "pip install -r requirements.txt"
      working_dir: "{path}"
      timeout: 600
      on_failure: "warn"

    - name: "Copy environment file"
      command: "cp ../.env .env"
      working_dir: "{path}"
      on_failure: "warn"

    - name: "Run database migrations"
      command: "python manage.py migrate"
      working_dir: "{path}"
      timeout: 300
      env:
        DATABASE_URL: "postgresql://localhost/dev_{branch}"
      on_failure: "abort"

  pre_switch:
    - name: "Auto-commit WIP changes"
      command: "git add -A && git commit -m 'WIP: auto-commit before switch' || true"
      working_dir: "{path}"
      on_failure: "continue"

  post_delete:
    - name: "Clean Python cache"
      command: "find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true"
      working_dir: "{path}"
      on_failure: "continue"

settings:
  auto_cleanup: true
  confirm_delete: true
  track_remote: true
```

## Validating Configuration

To check your configuration:

```bash
# Show merged configuration
wt config

# Show global configuration only
wt config --global

# Show project configuration only
wt config --project
```

## Common Patterns

### Python Projects

```yaml
hooks:
  post_create:
    - name: "Create virtual environment"
      command: "python -m venv venv"
      working_dir: "{path}"
      timeout: 120

    - name: "Install dependencies"
      command: "source venv/bin/activate && pip install -r requirements.txt"
      working_dir: "{path}"
      timeout: 600
```

### Node.js Projects

```yaml
hooks:
  post_create:
    - name: "Install npm packages"
      command: "npm install"
      working_dir: "{path}"
      timeout: 600

    - name: "Copy .env file"
      command: "cp ../.env.example .env"
      working_dir: "{path}"
```

### Go Projects

```yaml
hooks:
  post_create:
    - name: "Download Go modules"
      command: "go mod download"
      working_dir: "{path}"
      timeout: 300
```

### Multiple Languages (Monorepo)

```yaml
hooks:
  post_create:
    - name: "Install backend dependencies"
      command: "cd backend && pip install -r requirements.txt"
      working_dir: "{path}"
      timeout: 600

    - name: "Install frontend dependencies"
      command: "cd frontend && npm install"
      working_dir: "{path}"
      timeout: 600
```
