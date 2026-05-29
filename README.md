# github-repo-discovery

Utility script that scans a base directory for Git repositories, detects which ones have a GitHub remote origin, and moves them into a `github_repos/` subdirectory.

## Stack

Python 3 (standard library)

## Usage

```bash
python app.py /path/to/scan
```

The script will:
- Recursively scan directories for `.git` folders
- Detect GitHub remote origins
- Move GitHub repos to `github_repos/`
- Print a summary report

## License

MIT
