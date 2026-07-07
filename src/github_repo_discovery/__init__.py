"""GitHub Repo Discovery - detect and organize Git repositories by hosting platform."""

from github_repo_discovery.cli import (
    detect_platform,
    get_remote_origin,
    is_git_repo,
    main,
    move_repo,
    platform_folder_name,
)

__all__ = [
    "detect_platform",
    "get_remote_origin",
    "is_git_repo",
    "main",
    "move_repo",
    "platform_folder_name",
]
