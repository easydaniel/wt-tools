# Hooks Guide

Hooks are custom scripts that run automatically at different stages of the worktree lifecycle. They enable powerful automation and workflow customization.

## Hook Execution Model

Hooks run sequentially in the order defined. Each hook can:

- Execute any shell command
- Access environment variables
- Use variable substitution for dynamic values
- Control what happens on failure

### Execution Flow

```
1. Load configuration (global + project)
2. Filter hooks by type (post_create, pre_switch, post_delete)
3. For each hook:
   a. Substitute variables in command and paths
   b. Set environment variables
   c. Execute command with timeout
   d. Handle success or failure based on on_failure mode
4. Report overall status
```

## Hook Types

### post_create

Runs after creating a new worktree.

**Use cases**:
- Install dependencies
- Copy configuration files
- Run database migrations
- Build assets
- Initialize development environment

**Example**:
```yaml
hooks:
  post_create:
    - name: "Setup development environment"
      command: |
        python -m venv venv &&
        source venv/bin/activate &&
        pip install -r requirements.txt &&
        cp .env.example .env
      working_dir: "{path}"
      timeout: 600
      on_failure: "abort"
```

### pre_switch

Runs before switching from current worktree to another.

**Use cases**:
- Auto-commit WIP changes
- Clean build artifacts
- Save application state
- Stop development servers

**Example**:
```yaml
hooks:
  pre_switch:
    - name: "Save work in progress"
      command: |
        if [[ -n $(git status -s) ]]; then
          git add -A
          git commit -m "WIP: auto-save before switch $(date)"
        fi
      working_dir: "{path}"
      on_failure: "continue"
```

### post_delete

Runs after deleting a worktree.

**Use cases**:
- Clean up build artifacts
- Remove database instances
- Free up resources
- Archive logs

**Example**:
```yaml
hooks:
  post_delete:
    - name: "Cleanup artifacts"
      command: "rm -rf build/ dist/ *.egg-info"
      working_dir: "{path}"
      on_failure: "continue"
```

## Writing Effective Hooks

### 1. Use Meaningful Names

```yaml
# Good
- name: "Install Python dependencies from requirements.txt"

# Not as good
- name: "Setup"
```

### 2. Set Appropriate Timeouts

```yaml
# Quick operations
- name: "Copy .env file"
  command: "cp .env.example .env"
  timeout: 10

# Slow operations
- name: "Install all npm packages"
  command: "npm install"
  timeout: 600  # 10 minutes
```

### 3. Choose the Right Failure Mode

```yaml
# Critical: must succeed
- name: "Database migration"
  command: "python manage.py migrate"
  on_failure: "abort"

# Important but not critical
- name: "Install optional tools"
  command: "pip install dev-tools"
  on_failure: "warn"

# Best effort
- name: "Clean cache"
  command: "rm -rf .cache"
  on_failure: "continue"
```

### 4. Make Commands Robust

```yaml
# Handle missing files gracefully
- name: "Copy config if exists"
  command: "test -f config.yaml && cp config.yaml .config/ || echo 'No config to copy'"
  on_failure: "continue"

# Use absolute paths for clarity
- name: "Run tests"
  command: "pytest tests/"
  working_dir: "{path}"
```

### 5. Use Variable Substitution

```yaml
- name: "Create branch-specific database"
  command: "createdb myapp_{branch}"
  env:
    PGHOST: "localhost"
    PGUSER: "postgres"
```

## Common Hook Recipes

### Python Development

```yaml
hooks:
  post_create:
    # Virtual environment
    - name: "Create virtual environment"
      command: "python -m venv venv"
      timeout: 120

    # Dependencies
    - name: "Install dependencies"
      command: "source venv/bin/activate && pip install -r requirements.txt"
      timeout: 600
      on_failure: "abort"

    # Development dependencies
    - name: "Install dev dependencies"
      command: "source venv/bin/activate && pip install -r requirements-dev.txt"
      timeout: 300
      on_failure: "warn"

    # Environment
    - name: "Copy environment file"
      command: "cp ../.env.example .env"
      on_failure: "warn"

  pre_switch:
    - name: "Deactivate virtual environment"
      command: "deactivate 2>/dev/null || true"
      on_failure: "continue"
```

### Node.js Development

```yaml
hooks:
  post_create:
    - name: "Install npm packages"
      command: "npm install"
      timeout: 600
      on_failure: "abort"

    - name: "Build assets"
      command: "npm run build"
      timeout: 300
      on_failure: "warn"

  pre_switch:
    - name: "Stop dev server"
      command: "pkill -f 'node.*dev' || true"
      on_failure: "continue"
```

### Go Development

```yaml
hooks:
  post_create:
    - name: "Download Go modules"
      command: "go mod download"
      timeout: 300

    - name: "Verify modules"
      command: "go mod verify"
      timeout: 60

    - name: "Build project"
      command: "go build ./..."
      timeout: 300
      on_failure: "warn"
```

### Docker Development

```yaml
hooks:
  post_create:
    - name: "Build Docker images"
      command: "docker-compose build"
      timeout: 1200
      on_failure: "abort"

    - name: "Start containers"
      command: "docker-compose up -d"
      timeout: 300

  post_delete:
    - name: "Stop containers"
      command: "docker-compose down"
      timeout: 120
      on_failure: "continue"
```

### Database Migrations

```yaml
hooks:
  post_create:
    - name: "Run database migrations"
      command: "bundle exec rails db:migrate"
      timeout: 300
      env:
        RAILS_ENV: "development"
        DATABASE_NAME: "myapp_{branch}"
      on_failure: "abort"

    - name: "Seed database"
      command: "bundle exec rails db:seed"
      timeout: 600
      on_failure: "warn"
```

### Git LFS

```yaml
hooks:
  post_create:
    - name: "Pull Git LFS files"
      command: "git lfs pull"
      timeout: 600
      on_failure: "warn"
```

### Code Generation

```yaml
hooks:
  post_create:
    - name: "Generate code"
      command: "make generate"
      timeout: 300
      on_failure: "abort"

    - name: "Format generated code"
      command: "make format"
      timeout: 120
      on_failure: "continue"
```

## Multi-step Hooks

For complex setups, use multi-line commands:

```yaml
hooks:
  post_create:
    - name: "Full development setup"
      command: |
        set -e
        echo "Installing dependencies..."
        npm install

        echo "Building project..."
        npm run build

        echo "Starting database..."
        docker-compose up -d postgres

        echo "Running migrations..."
        npm run migrate

        echo "Setup complete!"
      working_dir: "{path}"
      timeout: 900
      on_failure: "abort"
```

## Conditional Hooks

Use shell conditions for flexible hooks:

```yaml
hooks:
  post_create:
    # Only install if requirements.txt exists
    - name: "Install Python dependencies"
      command: |
        if [ -f requirements.txt ]; then
          pip install -r requirements.txt
        else
          echo "No requirements.txt found, skipping..."
        fi
      timeout: 600
      on_failure: "continue"

    # Different commands for different branches
    - name: "Branch-specific setup"
      command: |
        case "{branch}" in
          main|master)
            echo "Production setup"
            npm run build:prod
            ;;
          develop)
            echo "Development setup"
            npm run build:dev
            ;;
          *)
            echo "Feature branch setup"
            npm run build
            ;;
        esac
      timeout: 300
```

## Environment Variables

Use environment variables for configuration:

```yaml
hooks:
  post_create:
    - name: "Deploy to staging"
      command: "kubectl apply -f k8s/"
      env:
        KUBECONFIG: "/home/user/.kube/staging"
        NAMESPACE: "app-{branch}"
      on_failure: "abort"
```

## Debugging Hooks

### Enable Verbose Output

```yaml
- name: "Debug installation"
  command: "set -x && npm install"  # -x shows each command
  timeout: 600
```

### Add Logging

```yaml
- name: "Install with logs"
  command: "npm install 2>&1 | tee install.log"
  timeout: 600
```

### Test Hooks Manually

```bash
# Test a hook command
cd /path/to/worktree
YOUR_HOOK_COMMAND_HERE
```

## Performance Tips

1. **Parallelize independent operations**:
```yaml
- name: "Install deps"
  command: "npm install & pip install -r requirements.txt & wait"
  timeout: 600
```

2. **Use caching**:
```yaml
- name: "Install with cache"
  command: "npm ci --cache .npm-cache"
```

3. **Skip unnecessary work**:
```yaml
- name: "Conditional build"
  command: "test -f dist/bundle.js || npm run build"
```

## Security Considerations

1. **Avoid hardcoded secrets**: Use environment variables
2. **Validate input**: Don't trust branch names blindly
3. **Use specific commands**: Avoid wildcards in destructive operations
4. **Review global hooks**: They run for all projects

## Troubleshooting

### Hook Times Out

Increase timeout or optimize the command:
```yaml
timeout: 1200  # Increase to 20 minutes
```

### Hook Fails Silently

Check the failure mode and add error handling:
```yaml
on_failure: "abort"  # Make failures visible
command: "npm install || (cat npm-debug.log && exit 1)"
```

### Variables Not Substituted

Ensure you're using the correct variable format:
```yaml
command: "echo {branch}"  # Correct
command: "echo $branch"   # Wrong (shell variable)
```

### Working Directory Issues

Use absolute paths or verify working_dir:
```yaml
working_dir: "{path}"  # Use worktree path
command: "pwd && ls -la"  # Debug current directory
```
