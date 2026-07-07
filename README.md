# GitHub Repo Discovery

Scan directories for Git repositories, detect their hosting platform (GitHub, GitLab, Bitbucket), and organize them into platform-specific subdirectories.

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![CI](https://github.com/bi0punk/github-repo-discovery/actions/workflows/ci.yml/badge.svg)](https://github.com/bi0punk/github-repo-discovery/actions/workflows/ci.yml)

## Features

- Recursive or top-level scanning for `.git` directories
- Detects remote `origin` pointing to GitHub, GitLab, or Bitbucket
- Proper URL parsing to avoid false positives (e.g. `notgithub.com`)
- Moves repos to platform-specific folders: `github_repos/`, `gitlab_repos/`, `bitbucket_repos/`
- `--dry-run` mode to preview changes without moving anything
- Critical system path protection with confirmation prompt
- Summary report with statistics per platform
- Zero runtime dependencies (Python standard library only)
- Installable as a CLI command via `pip install`

## Installation

```bash
pip install git+https://github.com/bi0punk/github-repo-discovery.git
```

Or for development:

```bash
git clone https://github.com/bi0punk/github-repo-discovery.git
cd github-repo-discovery
uv sync --all-extras
```

## Usage

```bash
github-repo-discovery /path/to/scan

# Dry-run: preview only, no changes
github-repo-discovery /path/to/scan --dry-run

# Recursive scanning
github-repo-discovery /path/to/scan --recursive

# Specific platforms only
github-repo-discovery /path/to/scan --platforms github.com,gitlab.com

# Verbose output
github-repo-discovery /path/to/scan -v

# As a Python module
python -m github_repo_discovery /path/to/scan --dry-run
```

### Example output

```
INFO  [DIR] my-project
INFO    Remote: https://github.com/user/my-project.git
INFO    Platform: github.com
INFO    Moved to: /home/user/projects/github_repos/my-project

INFO  [DIR] another-repo
INFO    Remote: https://gitlab.com/group/repo.git
INFO    Platform: gitlab.com
INFO    Moved to: /home/user/projects/gitlab_repos/another-repo

========================================
SUMMARY
========================================
Directories scanned: ~10
Git repositories:    5
  github.com: 3
  gitlab.com: 2
Repos moved: 5
Base directory: /home/user/projects
```

## Options

| Flag | Description |
|---|---|
| `--dry-run` | Report what would be moved without actually moving |
| `--recursive` | Recurse into subdirectories (default: top-level only) |
| `--platforms` | Comma-separated domains to detect (default: `github.com,gitlab.com,bitbucket.org`) |
| `--verbose`, `-v` | Enable debug-level logging |
| `--help`, `-h` | Show help |

## Project Structure

```
github-repo-discovery/
├── src/
│   └── github_repo_discovery/
│       ├── __init__.py
│       ├── __main__.py
│       └── cli.py              # CLI entry point and core logic
├── tests/
│   └── test_app.py             # 41 unit tests
├── .github/
│   └── workflows/
│       └── ci.yml              # CI: Ruff lint + pytest with coverage
├── pyproject.toml              # Project config, deps, entry points
├── .python-version             # Python version pin
├── LICENSE                     # MIT
└── README.md
```

## Requirements

- Python >= 3.11
- Git installed on the system

No external Python dependencies required at runtime.

## Tests

```bash
uv sync --all-extras
uv run pytest -v
uv run pytest --cov=src --cov-report=term-missing
```

## Limitations

- Only scans remote `origin` (not other remotes)
- Does not handle Git submodules
- Does not preserve extended file attributes
- Shell-like Git URLs (e.g. `git@github.com:user/repo.git`) are supported via SSH URL parsing

## License

MIT
