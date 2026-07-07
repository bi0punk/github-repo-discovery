from __future__ import annotations

import argparse
import logging
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger("repo-discovery")

CRITICAL_EXACT: set[str] = {"/", "/home", "/root", "/tmp"}
CRITICAL_PREFIX: set[str] = {"/etc/", "/sys/", "/proc/", "/dev/", "/boot/", "/var/"}

PLATFORM_DOMAINS: dict[str, str] = {
    "github.com": "github_repos",
    "gitlab.com": "gitlab_repos",
    "bitbucket.org": "bitbucket_repos",
}


def is_git_repo(path: Path) -> bool:
    """Check whether a directory contains a .git subdirectory."""
    return (path / ".git").is_dir()


def get_remote_origin(path: Path) -> str:
    """Return the remote origin URL for a Git repository.

    Args:
        path: Path to the repository root.

    Returns:
        The remote origin URL string, or empty string if none is configured
        or if git is unavailable.
    """
    if not path.is_dir():
        return ""
    try:
        result = subprocess.run(
            ["git", "-C", str(path), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        logger.warning("git command not found in PATH; cannot inspect remote URLs")
    except OSError as exc:
        logger.warning("OS error while running git on %s: %s", path, exc)
    return ""


def detect_platform(remote_url: str) -> str | None:
    """Detect the hosting platform from a remote URL.

    Parses the URL properly to avoid false positives from substrings
    (e.g. 'notgithub.com' or 'github.com.evil.com').

    Args:
        remote_url: The remote origin URL.

    Returns:
        Platform domain string (e.g. 'github.com') or None if unrecognized.
    """
    if not remote_url:
        return None
    try:
        parsed = urlparse(remote_url if "://" in remote_url else f"ssh://{remote_url}")
    except ValueError:
        remote_lower = remote_url.lower().strip()
        for domain in PLATFORM_DOMAINS:
            if f"@{domain}:" in remote_lower or remote_lower.startswith(f"{domain}:"):
                return domain
        return None

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        for domain in PLATFORM_DOMAINS:
            if f"@{domain}:" in remote_url.lower():
                return domain
        return None

    for domain in PLATFORM_DOMAINS:
        if hostname == domain or hostname.endswith(f".{domain}"):
            return domain
    return None


def move_repo(source: Path, destination_base: Path) -> bool:
    """Move a repository directory into a platform subdirectory.

    Args:
        source: Path to the repository to move.
        destination_base: Base directory of the destination platform folder.

    Returns:
        True if the move succeeded, False otherwise.
    """
    destination = destination_base / source.name
    if destination.exists():
        logger.warning("Destination already exists: %s", destination)
        return False
    try:
        shutil.move(str(source), str(destination))
        logger.info("Moved to: %s", destination)
        return True
    except OSError as exc:
        logger.error("Failed to move %s: %s", source, exc)
        return False


def _warn_critical_path(base_dir: Path) -> bool:
    """Warn and confirm if the base directory looks like a critical system path.

    Returns True if safe to proceed, False if user aborts.
    """
    resolved = str(base_dir)
    if resolved in CRITICAL_EXACT or any(
        resolved.startswith(prefix) for prefix in CRITICAL_PREFIX
    ):
        logger.warning("The path '%s' looks like a critical system directory.", resolved)
        try:
            answer = input("Proceed anyway? [y/N] ").strip().lower()
            if answer not in ("y", "yes"):
                logger.info("Aborted by user.")
                return False
        except (EOFError, KeyboardInterrupt):
            return False
    return True


def _collect_repos(
    base_dir: Path, recursive: bool, platforms: set[str] | None = None
) -> list[tuple[Path, str | None]]:
    """Collect repositories and their detected platforms.

    Args:
        base_dir: Base directory to scan.
        recursive: Whether to recurse into subdirectories.
        platforms: Set of platform domains to consider, or None for all.

    Returns:
        List of (path, platform_or_None) tuples.
    """
    if platforms is None:
        platforms = set(PLATFORM_DOMAINS.keys())

    pattern = "**/" if recursive else "*/"
    results: list[tuple[Path, str | None]] = []
    seen: set[str] = set()

    for item in sorted(base_dir.glob(pattern)):
        if not item.is_dir():
            continue
        item = item.resolve()

        item_str = str(item)
        if item_str in seen or item.relative_to(base_dir) == Path("."):
            continue
        seen.add(item_str)

        if "github_repos" in str(item.relative_to(base_dir)).split("/")[0:1]:
            continue
        if "gitlab_repos" in str(item.relative_to(base_dir)).split("/")[0:1]:
            continue
        if "bitbucket_repos" in str(item.relative_to(base_dir)).split("/")[0:1]:
            continue

        if not is_git_repo(item):
            continue

        remote = get_remote_origin(item)
        platform = detect_platform(remote)

        if platform is None or platform not in platforms:
            results.append((item, None))
        else:
            results.append((item, platform))

    return results


def main(argv: list[str] | None = None) -> None:
    """Entry point for the CLI tool."""
    parser = argparse.ArgumentParser(
        description="Scan directories for Git repos and organize by hosting platform.",
    )
    parser.add_argument("directory", type=str, nargs="?", help="Base directory to scan")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be moved without actually moving anything",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recurse into subdirectories (default: top-level only)",
    )
    parser.add_argument(
        "--platforms",
        type=str,
        default="github.com,gitlab.com,bitbucket.org",
        help="Comma-separated platform domains to detect (default: github.com,gitlab.com,bitbucket.org)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug-level logging",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)-5s %(message)s",
    )

    if not args.directory:
        parser.print_help()
        sys.exit(1)

    base_dir = Path(args.directory).expanduser().resolve()

    if not base_dir.exists() or not base_dir.is_dir():
        logger.error("Invalid path: %s", base_dir)
        sys.exit(1)

    if not _warn_critical_path(base_dir):
        sys.exit(1)

    platforms = {p.strip().lower() for p in args.platforms.split(",") if p.strip()}
    repos = _collect_repos(base_dir, args.recursive, platforms)
    if not repos:
        logger.info("No Git repositories found in %s", base_dir)
        return

    total_dirs = sum(1 for _ in sorted(base_dir.glob("**/" if args.recursive else "*/")))
    total_git = len(repos)
    total_platform: dict[str, int] = {}
    moved = 0

    domain_to_folder: dict[str, str] = {}
    for domain in platforms:
        domain_to_folder[domain] = platform_folder_name(domain)

    for item, platform in repos:
        logger.info("[DIR] %s", item.name)
        remote = get_remote_origin(item)

        if remote:
            logger.info("  Remote: %s", remote)
        else:
            logger.info("  Remote: (none)")

        if platform is None:
            logger.info("  Result: non-matched Git repo, skipping")
        else:
            logger.info("  Platform: %s", platform)
            total_platform[platform] = total_platform.get(platform, 0) + 1

            if not args.dry_run:
                dest = base_dir / domain_to_folder.get(platform, f"{platform.replace('.', '_')}_repos")
                dest.mkdir(exist_ok=True)
                if move_repo(item, dest):
                    moved += 1
            else:
                logger.info("  [DRY-RUN] Would move to: %s/%s",
                            domain_to_folder.get(platform, f"{platform.replace('.', '_')}_repos"), item.name)
                moved += 1

    logger.info("")
    logger.info("=" * 40)
    logger.info("SUMMARY")
    logger.info("=" * 40)
    logger.info("Directories scanned: ~%d", total_dirs)
    logger.info("Git repositories:    %d", total_git)
    for domain, count in sorted(total_platform.items()):
        logger.info("  %s: %d", domain, count)
    logger.info("Repos %s: %d", "would be moved" if args.dry_run else "moved", moved)
    logger.info("Base directory: %s", base_dir)


def platform_folder_name(domain: str) -> str:
    """Convert a platform domain into a directory name."""
    mapping = {
        "github.com": "github_repos",
        "gitlab.com": "gitlab_repos",
        "bitbucket.org": "bitbucket_repos",
    }
    return mapping.get(domain, f"{domain.replace('.', '_')}_repos")
