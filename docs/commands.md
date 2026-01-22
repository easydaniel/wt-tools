# Command Reference

Complete reference for all wt-tools CLI commands.

## Global Options

```bash
wt --help     # Show help
wt --version  # Show version
```

## Commands

### wt init

Initialize wt-tools configuration.

**Usage:**
```bash
wt init [--global]
```

**Options:**
- `--global`: Create global config instead of project config

**Examples:**
```bash
# Create project configuration
wt init

# Create global configuration
wt init --global
```

**What it does:**
1. Creates configuration file with default template
2. Prompts to add patterns to `.gitignore`
3. Shows next steps

---

### wt create

Create a new worktree for a branch.

**Usage:**
```bash
wt create BRANCH [--path PATH] [--skip-hooks]
```

**Arguments:**
- `BRANCH`: Branch name (created if doesn't exist)

**Options:**
- `--path PATH`: Custom worktree path (overrides config)
- `--skip-hooks`: Don't run post_create hooks

**Examples:**
```bash
# Create worktree for new branch
wt create feature/new-feature

# Create worktree at custom path
wt create bugfix/issue-123 --path /tmp/bugfix

# Create worktree without running hooks
wt create experiment --skip-hooks
```

**What it does:**
1. Checks if worktree already exists
2. Determines worktree path from config
3. Prompts to update `.gitignore` if needed
4. Creates worktree using `git worktree add`
5. Runs post_create hooks (unless --skip-hooks)

---

### wt list

List all worktrees.

**Usage:**
```bash
wt list [--verbose]
```

**Options:**
- `--verbose`, `-v`: Show additional information (status, size)

**Examples:**
```bash
# List all worktrees
wt list

# List with detailed information
wt list --verbose
wt list -v
```

**Output:**
- Branch name
- Worktree path
- Current commit (short hash)
- Status (clean/modified) - verbose only
- Disk usage - verbose only
- `*` marker for current worktree

---

### wt switch

Switch to a worktree.

**Usage:**
```bash
cd $(wt switch BRANCH)
```

**Arguments:**
- `BRANCH`: Branch name to switch to

**Examples:**
```bash
# Switch to a worktree
cd $(wt switch feature/new-feature)

# Create shell alias for convenience
alias wts='cd $(wt switch $1)'
wts feature/new-feature
```

**What it does:**
1. Runs pre_switch hooks in current worktree
2. Prints path to target worktree
3. User must use `cd $()` to actually change directory

**Note:** The command only prints the path because a subprocess cannot change the parent shell's working directory.

---

### wt delete

Delete a worktree.

**Usage:**
```bash
wt delete BRANCH [--force] [--keep-branch]
```

**Arguments:**
- `BRANCH`: Branch name of worktree to delete

**Options:**
- `--force`, `-f`: Skip confirmations and ignore uncommitted changes
- `--keep-branch`: Delete worktree but keep the branch

**Examples:**
```bash
# Delete worktree (with confirmation)
wt delete feature/old-feature

# Delete worktree without confirmation
wt delete feature/old-feature --force

# Delete worktree but keep the branch
wt delete feature/wip --keep-branch
```

**What it does:**
1. Checks for uncommitted changes (unless --force)
2. Prompts for confirmation (unless --force or confirm_delete=false)
3. Runs post_delete hooks
4. Removes worktree
5. Deletes branch (unless --keep-branch)

**Safety:**
- Cannot delete main worktree
- Warns if there are uncommitted changes
- Asks for confirmation by default

---

### wt config

Show configuration.

**Usage:**
```bash
wt config [--global | --project]
```

**Options:**
- `--global`: Show only global configuration
- `--project`: Show only project configuration
- (no flag): Show merged configuration

**Examples:**
```bash
# Show merged configuration
wt config

# Show global configuration
wt config --global

# Show project configuration
wt config --project
```

**Output:**
- YAML-formatted configuration
- Syntax highlighting
- Shows effective configuration after merging

---

### wt cleanup

Clean up stale worktrees.

**Usage:**
```bash
wt cleanup [--dry-run]
```

**Options:**
- `--dry-run`: Show what would be cleaned without actually doing it

**Examples:**
```bash
# Preview cleanup
wt cleanup --dry-run

# Actually clean up
wt cleanup
```

**What it does:**
- Removes administrative files for worktrees that no longer exist
- Useful after manually deleting worktree directories

---

## Common Workflows

### Starting New Feature

```bash
# Create worktree for new feature branch
wt create feature/awesome-feature

# Switch to it
cd $(wt switch feature/awesome-feature)

# Work on feature...
git add .
git commit -m "Add awesome feature"

# Switch back to main
cd $(wt switch main)

# Delete feature worktree when done
wt delete feature/awesome-feature
```

### Quick Bug Fix

```bash
# Create worktree from custom path
wt create hotfix/critical-bug --path /tmp/hotfix

# Fix the bug
cd /tmp/hotfix
# ... make changes ...
git commit -am "Fix critical bug"

# Push and create PR
git push -u origin hotfix/critical-bug

# Clean up
wt delete hotfix/critical-bug --force
```

### Parallel Development

```bash
# Create multiple worktrees
wt create feature/frontend
wt create feature/backend
wt create feature/docs

# List all worktrees
wt list

# Work on different features in different terminals
# Terminal 1: cd $(wt switch feature/frontend)
# Terminal 2: cd $(wt switch feature/backend)
# Terminal 3: cd $(wt switch feature/docs)
```

### Review Someone's PR

```bash
# Create worktree for PR branch
wt create pr-review/feat-auth

cd $(wt switch pr-review/feat-auth)
git fetch origin pull/123/head
git checkout FETCH_HEAD

# Review code...

# Clean up
wt delete pr-review/feat-auth --force
```

## Shell Integration

### Bash/Zsh Alias

Add to `.bashrc` or `.zshrc`:

```bash
# Quick switch
alias wts='cd $(wt switch $1)'

# Create and switch
wtc() {
  wt create "$1" && cd $(wt switch "$1")
}

# List worktrees
alias wtl='wt list'

# Delete with confirmation
alias wtd='wt delete'
```

### Fish Shell

Add to `~/.config/fish/config.fish`:

```fish
# Quick switch
function wts
    cd (wt switch $argv[1])
end

# Create and switch
function wtc
    wt create $argv[1]; and cd (wt switch $argv[1])
end
```

## Exit Codes

All commands follow standard exit code conventions:

- `0`: Success
- `1`: Error (check error message)
- `2`: Invalid usage (check --help)

## Environment Variables

wt-tools respects these environment variables:

- `GIT_DIR`: Custom git directory
- `GIT_WORK_TREE`: Custom working tree
- Standard shell variables (`HOME`, `USER`, etc.)

## Tips and Tricks

### List Worktrees by Size

```bash
wt list --verbose | sort -k5 -h
```

### Find Worktrees with Uncommitted Changes

```bash
wt list --verbose | grep modified
```

### Bulk Delete Worktrees

```bash
for branch in $(git branch --format='%(refname:short)' | grep 'feature/old-'); do
  wt delete "$branch" --force
done
```

### Create Worktree from Remote Branch

```bash
git fetch origin
wt create feature/from-remote
cd $(wt switch feature/from-remote)
git reset --hard origin/feature/from-remote
```
