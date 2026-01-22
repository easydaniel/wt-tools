# Deployment Guide for wt-tools

## Current Status

✅ Package built and validated
✅ Git repository initialized
✅ Initial commit created
✅ Version tag (v0.1.0) created
✅ Author info updated (easydaniel / tanchien1335@gmail.com)

## Next Steps

### 1. Create GitHub Repository

#### Option A: Using GitHub CLI (gh)

```bash
# Install gh if needed: brew install gh (macOS) or see https://cli.github.com/

# Authenticate with GitHub
gh auth login

# Create repository
gh repo create wt-tools --public --source=. --remote=origin

# Push code
git push -u origin main --tags
```

#### Option B: Using GitHub Web Interface

1. Go to https://github.com/new
2. Repository name: `wt-tools`
3. Description: `Git worktree management with configurable hooks`
4. Set to **Public**
5. **Don't** initialize with README, .gitignore, or license (already have them)
6. Click "Create repository"
7. Run these commands:

```bash
git remote add origin https://github.com/easydaniel/wt-tools.git
git push -u origin main
git push --tags
```

### 2. Set Up PyPI Publishing

#### Get PyPI API Token

1. Create PyPI account at https://pypi.org/account/register/
2. Verify your email
3. Go to https://pypi.org/manage/account/token/
4. Click "Add API token"
   - Token name: `wt-tools-publishing`
   - Scope: Select "Entire account" for now (can narrow after first upload)
5. Copy the token (starts with `pypi-`)

#### Add Token to GitHub Secrets

1. Go to your repository: https://github.com/easydaniel/wt-tools
2. Click Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `PYPI_API_TOKEN`
5. Value: Paste your PyPI token
6. Click "Add secret"

#### Publish to PyPI

##### Option A: Automatic via GitHub Release (Recommended)

1. Go to https://github.com/easydaniel/wt-tools/releases
2. Click "Create a new release"
3. Click "Choose a tag" → Select `v0.1.0`
4. Release title: `v0.1.0 - Initial Release`
5. Description: Copy from CHANGELOG.md
6. Click "Publish release"
7. GitHub Actions will automatically publish to PyPI

##### Option B: Manual Upload

```bash
# Make sure you're in the project directory
cd /Users/tanchien/Documents/wt-tools

# Activate virtual environment
source venv/bin/activate

# Upload to PyPI
twine upload dist/*

# Enter your PyPI username and API token when prompted
# Username: __token__
# Password: <your-pypi-token>
```

### 3. Verify Installation

After publishing, test the installation:

```bash
# Create a new virtual environment for testing
python -m venv test-env
source test-env/bin/activate

# Install from PyPI
pip install wt-tools

# Test the command
wt --version
wt --help

# Clean up
deactivate
rm -rf test-env
```

### 4. Post-Release Tasks

#### Update Repository Settings

1. Go to repository Settings
2. Add topics: `git`, `worktree`, `cli`, `python`, `automation`
3. Add description: "Git worktree management with configurable hooks"
4. Add website: https://pypi.org/project/wt-tools/

#### Enable GitHub Actions (if needed)

1. Go to Actions tab
2. If prompted, enable GitHub Actions
3. Workflows should run automatically on push and releases

#### Create GitHub README Badges

Add to the top of README.md:

```markdown
# wt-tools

[![PyPI version](https://badge.fury.io/py/wt-tools.svg)](https://badge.fury.io/py/wt-tools)
[![Tests](https://github.com/easydaniel/wt-tools/actions/workflows/test.yml/badge.svg)](https://github.com/easydaniel/wt-tools/actions/workflows/test.yml)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
```

### 5. Share Your Project

- Post on Reddit: r/Python, r/git
- Post on Hacker News
- Share on Twitter/X with hashtags: #Python #Git #CLI
- Add to awesome-python lists
- Write a blog post about the tool

## Troubleshooting

### GitHub Push Issues

If you get authentication errors:

```bash
# Use GitHub CLI
gh auth login

# Or use SSH instead of HTTPS
git remote set-url origin git@github.com:easydaniel/wt-tools.git
```

### PyPI Upload Issues

**Error: "File already exists"**
- You can't re-upload the same version
- Increment version in `wt_tools/__init__.py` and `pyproject.toml`
- Rebuild: `python -m build`
- Upload again: `twine upload dist/*`

**Error: "Invalid credentials"**
- Make sure username is `__token__` (with underscores)
- Token must start with `pypi-`
- Regenerate token if needed

### Package Testing Issues

If installation fails:
```bash
# Try installing in editable mode first
pip install -e .

# Check for dependency issues
pip check
```

## Useful Commands

```bash
# Check current git status
git status

# View commit history
git log --oneline --decorate

# List tags
git tag -l

# Create new release
git tag -a v0.2.0 -m "Release v0.2.0"
git push --tags

# Build package
python -m build

# Check package
twine check dist/*

# Upload to PyPI
twine upload dist/*
```

## Resources

- PyPI Dashboard: https://pypi.org/manage/projects/
- GitHub Repository: https://github.com/easydaniel/wt-tools
- Python Packaging Guide: https://packaging.python.org/
- Semantic Versioning: https://semver.org/

## Support

If you encounter any issues:
1. Check GitHub Issues: https://github.com/easydaniel/wt-tools/issues
2. Review GitHub Actions logs
3. Check PyPI project page for upload status
