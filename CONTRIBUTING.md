# Contributing to wt-tools

Thank you for your interest in contributing to wt-tools! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful and constructive in all interactions.

## Getting Started

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/easydaniel/wt-tools.git
cd wt-tools
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode:
```bash
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=wt_tools --cov-report=html

# Run specific test file
pytest tests/test_config.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code
black wt_tools tests

# Lint code
flake8 wt_tools tests

# Type checking
mypy wt_tools
```

## Making Changes

### Branching Strategy

- Create a new branch for your feature/fix
- Use descriptive branch names:
  - `feature/add-new-command`
  - `fix/handle-edge-case`
  - `docs/improve-readme`

### Commit Messages

Follow conventional commit format:

```
<type>(<scope>): <short description>

<optional body>

<optional footer>
```

Types:
- `feature`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions or modifications
- `refactor`: Code refactoring
- `core`: Build, tooling, dependencies

Examples:
```
feature(hooks): add support for environment variables

fix(cli): handle missing .gitignore gracefully

docs(readme): add installation instructions
```

### Pull Request Process

1. Update documentation if needed
2. Add tests for new functionality
3. Ensure all tests pass
4. Update CHANGELOG.md with your changes
5. Create a pull request with clear description

## Project Structure

```
wt-tools/
├── wt_tools/          # Main package
│   ├── cli.py         # CLI commands
│   ├── config.py      # Configuration management
│   ├── worktree.py    # Worktree operations
│   ├── hooks.py       # Hook execution
│   └── gitignore.py   # Gitignore utilities
├── tests/             # Test suite
├── docs/              # Documentation
├── examples/          # Example configurations
└── pyproject.toml     # Package configuration
```

## Testing Guidelines

- Write tests for all new features
- Maintain or improve code coverage
- Use descriptive test names
- Test both success and failure paths

## Documentation

- Update README.md for user-facing changes
- Add docstrings to all functions and classes
- Update docs/ for new features or changed behavior
- Add examples when appropriate

## Release Process

1. Update version in `wt_tools/__init__.py`
2. Update CHANGELOG.md
3. Create a git tag: `git tag v0.x.0`
4. Push tag: `git push --tags`
5. GitHub Actions will automatically publish to PyPI

## Questions?

Open an issue for:
- Bug reports
- Feature requests
- Questions about usage or development

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
