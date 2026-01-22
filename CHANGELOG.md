# Changelog

All notable changes to wt-tools will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-22

### Added
- Initial release of wt-tools
- Core worktree management commands (`create`, `list`, `delete`, `switch`, `cleanup`)
- Configuration system with global and project-level configs
- Hook system with `post_create`, `pre_switch`, and `post_delete` hooks
- Automatic .gitignore management with fallback paths
- Rich terminal output with progress indicators and formatted tables
- Comprehensive test suite with 78% coverage
- Complete documentation including configuration, hooks, and command references
- Example configurations for Python, Node.js, and Docker projects
- GitHub Actions workflows for testing and publishing

### Features
- Variable substitution in config and hooks (`{branch}`, `{path}`, `{project}`, etc.)
- Multiple hook failure modes (abort, continue, warn)
- Environment variable support in hooks
- Timeout configuration for hooks
- Customizable worktree directory paths
- Confirmation prompts for destructive operations
- Verbose mode for detailed worktree information

[0.1.0]: https://github.com/easydaniel/wt-tools/releases/tag/v0.1.0
