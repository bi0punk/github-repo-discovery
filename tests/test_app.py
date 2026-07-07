import os
from pathlib import Path
from unittest import mock

import pytest

from github_repo_discovery.cli import (
    _collect_repos,
    _warn_critical_path,
    detect_platform,
    get_remote_origin,
    is_git_repo,
    main,
    move_repo,
    platform_folder_name,
)


class TestIsGitRepo:
    def test_returns_true_if_dotgit_exists(self, tmp_path):
        repo = tmp_path / "myrepo"
        repo.mkdir()
        (repo / ".git").mkdir()
        assert is_git_repo(repo) is True

    def test_returns_false_if_no_dotgit(self, tmp_path):
        repo = tmp_path / "myrepo"
        repo.mkdir()
        assert is_git_repo(repo) is False

    def test_returns_false_if_dotgit_is_file(self, tmp_path):
        repo = tmp_path / "myrepo"
        repo.mkdir()
        (repo / ".git").write_text("fake")
        assert is_git_repo(repo) is False


class TestGetRemoteOrigin:
    def test_returns_url_on_success(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="https://github.com/user/repo.git\n")
            result = get_remote_origin(repo)
            assert result == "https://github.com/user/repo.git"

    def test_returns_empty_on_nonzero_returncode(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=1, stdout="")
            result = get_remote_origin(repo)
            assert result == ""

    def test_returns_empty_if_path_not_dir(self):
        result = get_remote_origin(Path("/nonexistent/path"))
        assert result == ""

    def test_returns_empty_if_git_not_found(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        with mock.patch("subprocess.run", side_effect=FileNotFoundError()):
            result = get_remote_origin(repo)
            assert result == ""

    def test_returns_empty_on_oserror(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        with mock.patch("subprocess.run", side_effect=OSError("permission denied")):
            result = get_remote_origin(repo)
            assert result == ""


class TestDetectPlatform:
    def test_detects_github_https(self):
        assert detect_platform("https://github.com/user/repo.git") == "github.com"

    def test_detects_github_ssh(self):
        assert detect_platform("git@github.com:user/repo.git") == "github.com"

    def test_detects_gitlab_https(self):
        assert detect_platform("https://gitlab.com/group/repo.git") == "gitlab.com"

    def test_detects_bitbucket_https(self):
        assert detect_platform("https://bitbucket.org/team/repo.git") == "bitbucket.org"

    def test_rejects_notgithub_com(self):
        assert detect_platform("https://notgithub.com/user/repo.git") is None

    def test_rejects_github_com_evil(self):
        assert detect_platform("https://github.com.evil.com/user/repo.git") is None

    def test_detects_github_enterprise_subdomain(self):
        assert detect_platform("https://git.mycompany.github.com/repo.git") == "github.com"

    def test_returns_none_for_empty_string(self):
        assert detect_platform("") is None

    def test_returns_none_for_unrecognized_url(self):
        assert detect_platform("https://codeberg.org/user/repo.git") is None


class TestMoveRepo:
    def test_moves_directory_successfully(self, tmp_path):
        source = tmp_path / "myrepo"
        source.mkdir()
        dest_base = tmp_path / "destination"
        dest_base.mkdir()

        assert move_repo(source, dest_base) is True
        assert not source.exists()
        assert (dest_base / "myrepo").is_dir()

    def test_returns_false_when_destination_exists(self, tmp_path):
        source = tmp_path / "myrepo"
        source.mkdir()
        dest_base = tmp_path / "destination"
        dest_base.mkdir()
        (dest_base / "myrepo").mkdir()

        assert move_repo(source, dest_base) is False
        assert source.exists()


class TestPlatformFolderName:
    def test_github(self):
        assert platform_folder_name("github.com") == "github_repos"

    def test_gitlab(self):
        assert platform_folder_name("gitlab.com") == "gitlab_repos"

    def test_bitbucket(self):
        assert platform_folder_name("bitbucket.org") == "bitbucket_repos"

    def test_custom_domain(self):
        assert platform_folder_name("codeberg.org") == "codeberg_org_repos"


class TestWarnCriticalPath:
    def test_allows_normal_path(self, tmp_path):
        assert _warn_critical_path(tmp_path) is True

    def test_warns_for_etc_with_yes(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _: "y")
        assert _warn_critical_path(Path("/etc/test")) is True

    def test_aborts_for_etc_with_no(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _: "n")
        assert _warn_critical_path(Path("/etc/test")) is False

    def test_aborts_for_root_path_with_eof(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _: (_ for _ in ()).throw(EOFError))
        assert _warn_critical_path(Path("/etc/foo")) is False


class TestCollectRepos:
    def test_finds_github_repo(self, tmp_path):
        repo = tmp_path / "myrepo"
        repo.mkdir()
        (repo / ".git").mkdir()

        with mock.patch("github_repo_discovery.cli.get_remote_origin") as mock_remote:
            mock_remote.return_value = "https://github.com/user/repo.git"
            results = _collect_repos(tmp_path, recursive=False, platforms={"github.com"})

        assert len(results) == 1
        assert results[0][0] == repo
        assert results[0][1] == "github.com"

    def test_skips_non_git_dirs(self, tmp_path):
        (tmp_path / "notrepo").mkdir()

        results = _collect_repos(tmp_path, recursive=False)
        assert len(results) == 0

    def test_skips_platform_folders(self, tmp_path):
        dest = tmp_path / "github_repos"
        dest.mkdir()
        (dest / ".git").mkdir()

        results = _collect_repos(tmp_path, recursive=False)
        assert len(results) == 0

    def test_returns_none_platform_for_unmatched(self, tmp_path):
        repo = tmp_path / "unknown"
        repo.mkdir()
        (repo / ".git").mkdir()

        with mock.patch("github_repo_discovery.cli.get_remote_origin") as mock_remote:
            mock_remote.return_value = "https://codeberg.org/user/repo.git"
            results = _collect_repos(tmp_path, recursive=False)

        assert len(results) == 1
        assert results[0][1] is None


class TestMainIntegration:
    def test_main_help_flag(self, capsys):
        with pytest.raises(SystemExit):
            main(["--help"])
        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower() or "usage:" in captured.out

    def test_main_no_args_shows_help(self, capsys):
        with pytest.raises(SystemExit):
            main([])

    def test_main_invalid_path_exits(self):
        with pytest.raises(SystemExit):
            main(["/nonexistent/path/xyz"])

    def test_main_dry_run_does_not_move(self, tmp_path, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _: "y")
        repo = tmp_path / "myrepo"
        repo.mkdir()
        (repo / ".git").mkdir()

        with mock.patch("github_repo_discovery.cli.get_remote_origin") as mock_remote:
            mock_remote.return_value = "https://github.com/user/repo.git"
            main([str(tmp_path), "--dry-run"])

        assert repo.exists()
        assert not (tmp_path / "github_repos").exists()

    def test_main_moves_repos(self, tmp_path, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _: "y")
        repo = tmp_path / "myrepo"
        repo.mkdir()
        (repo / ".git").mkdir()

        with mock.patch("github_repo_discovery.cli.get_remote_origin") as mock_remote:
            mock_remote.return_value = "https://github.com/user/repo.git"
            main([str(tmp_path)])

        assert not repo.exists()
        assert (tmp_path / "github_repos" / "myrepo").is_dir()

    def test_main_no_repos_found_returns_cleanly(self, tmp_path, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _: "y")
        main([str(tmp_path)])

    def test_main_verbose_flag_runs(self, tmp_path, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _: "y")
        (tmp_path / "dummy").mkdir()
        main([str(tmp_path), "-v"])


def test_smoke_readme_exists():
    assert os.path.isfile("README.md")


def test_smoke_gitignore_exists():
    assert os.path.isfile(".gitignore")


def test_smoke_pyproject_exists():
    assert os.path.isfile("pyproject.toml")
