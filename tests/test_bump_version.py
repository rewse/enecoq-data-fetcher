"""Tests for scripts/bump_version.sh."""

import os
import pathlib
import shutil
import subprocess
import tempfile

SCRIPT = pathlib.Path(__file__).resolve().parent.parent / "scripts" / "bump_version.sh"
VERSION_FILE = pathlib.Path("src") / "enecoq_data_fetcher" / "__init__.py"

# Isolate git from the user's global config, such as commit signing.
GIT_ENV = dict(
    os.environ,
    GIT_CONFIG_GLOBAL=os.devnull,
    GIT_CONFIG_NOSYSTEM="1",
    GIT_AUTHOR_NAME="Test",
    GIT_AUTHOR_EMAIL="test@example.com",
    GIT_COMMITTER_NAME="Test",
    GIT_COMMITTER_EMAIL="test@example.com",
)


def _git(repo, *args):
    """Run git in repo and return its stdout."""
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        env=GIT_ENV,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _make_repo(tmpdir):
    """Create a work repository at version 1.2.3 pushed to a bare origin.

    Args:
        tmpdir: Directory to create the repositories in.

    Returns:
        Path to the work repository.
    """
    origin = pathlib.Path(tmpdir) / "origin.git"
    work = pathlib.Path(tmpdir) / "work"
    subprocess.run(
        ["git", "init", "--quiet", "--bare", "-b", "main", str(origin)],
        env=GIT_ENV,
        check=True,
    )
    subprocess.run(
        ["git", "init", "--quiet", "-b", "main", str(work)],
        env=GIT_ENV,
        check=True,
    )
    (work / "scripts").mkdir()
    shutil.copy(SCRIPT, work / "scripts" / "bump_version.sh")
    (work / VERSION_FILE).parent.mkdir(parents=True)
    (work / VERSION_FILE).write_text('__version__ = "1.2.3"\n', encoding="utf-8")
    _git(work, "add", ".")
    _git(work, "commit", "--quiet", "-m", "initial")
    _git(work, "remote", "add", "origin", str(origin))
    _git(work, "push", "--quiet", "-u", "origin", "main")
    return work


def _bump(work, *args):
    """Run the copied script in the work repository."""
    return subprocess.run(
        ["bash", "scripts/bump_version.sh", *args],
        cwd=work,
        env=GIT_ENV,
        capture_output=True,
        text=True,
    )


def _version(work):
    """Return the version line of the work repository."""
    return (work / VERSION_FILE).read_text(encoding="utf-8").strip()


def test_bump_patch_commits_and_tags():
    """Test that a patch bump commits only the version file and tags it."""
    with tempfile.TemporaryDirectory() as tmpdir:
        work = _make_repo(tmpdir)

        result = _bump(work, "patch")

        assert result.returncode == 0, result.stderr
        assert _version(work) == '__version__ = "1.2.4"'
        assert _git(work, "log", "-1", "--format=%s") == "chore: bump version to 1.2.4"
        assert _git(work, "show", "--name-only", "--format=", "HEAD") == str(
            VERSION_FILE
        )
        assert _git(work, "tag", "--list") == "v1.2.4"
        assert _git(work, "ls-remote", "--tags", "origin") == ""
    print("✓ Bump patch commits and tags test passed")


def test_bump_minor_and_major_reset_lower_parts():
    """Test that minor and major bumps reset the lower version parts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        work = _make_repo(tmpdir)
        assert _bump(work, "minor").returncode == 0
        assert _version(work) == '__version__ = "1.3.0"'
        _git(work, "push", "--quiet", "origin", "main")
        assert _bump(work, "major").returncode == 0
        assert _version(work) == '__version__ = "2.0.0"'
    print("✓ Bump minor and major test passed")


def test_bump_with_push_sends_branch_and_tag():
    """Test that --push sends main and only the new tag."""
    with tempfile.TemporaryDirectory() as tmpdir:
        work = _make_repo(tmpdir)
        _git(work, "tag", "local-only")

        result = _bump(work, "patch", "--push")

        assert result.returncode == 0, result.stderr
        remote_tags = _git(work, "ls-remote", "--tags", "origin")
        assert "refs/tags/v1.2.4" in remote_tags
        assert "local-only" not in remote_tags
        assert _git(work, "rev-parse", "origin/main") == _git(work, "rev-parse", "HEAD")
    print("✓ Bump with push test passed")


def _assert_refused(work, result, head_before):
    """Assert that the script stopped without changing anything."""
    assert result.returncode != 0
    assert _version(work) == '__version__ = "1.2.3"'
    assert _git(work, "rev-parse", "HEAD") == head_before
    assert "v1.2.4" not in _git(work, "tag", "--list")


def test_bump_refuses_unclean_tree():
    """Test that staged, modified, or untracked files stop the release."""
    with tempfile.TemporaryDirectory() as tmpdir:
        work = _make_repo(tmpdir)
        head = _git(work, "rev-parse", "HEAD")

        (work / "notes.txt").write_text("draft\n", encoding="utf-8")
        _assert_refused(work, _bump(work, "patch"), head)

        _git(work, "add", "notes.txt")
        _assert_refused(work, _bump(work, "patch"), head)
    print("✓ Bump refuses unclean tree test passed")


def test_bump_refuses_other_branch():
    """Test that releasing from a branch other than main is refused."""
    with tempfile.TemporaryDirectory() as tmpdir:
        work = _make_repo(tmpdir)
        _git(work, "switch", "--quiet", "-c", "feature")
        head = _git(work, "rev-parse", "HEAD")

        _assert_refused(work, _bump(work, "patch"), head)
    print("✓ Bump refuses other branch test passed")


def test_bump_refuses_unpushed_commit():
    """Test that a local commit not on origin/main is refused."""
    with tempfile.TemporaryDirectory() as tmpdir:
        work = _make_repo(tmpdir)
        _git(work, "commit", "--quiet", "--allow-empty", "-m", "unpushed")
        head = _git(work, "rev-parse", "HEAD")

        _assert_refused(work, _bump(work, "patch"), head)
    print("✓ Bump refuses unpushed commit test passed")


def test_bump_refuses_existing_tag():
    """Test that an existing tag for the new version is refused."""
    with tempfile.TemporaryDirectory() as tmpdir:
        work = _make_repo(tmpdir)
        _git(work, "tag", "v1.2.4")
        _git(work, "push", "--quiet", "origin", "v1.2.4")
        _git(work, "tag", "--delete", "v1.2.4")
        head = _git(work, "rev-parse", "HEAD")

        result = _bump(work, "patch")

        assert result.returncode != 0
        assert _version(work) == '__version__ = "1.2.3"'
        assert _git(work, "rev-parse", "HEAD") == head
    print("✓ Bump refuses existing tag test passed")


def test_bump_refuses_invalid_arguments():
    """Test that an unknown bump type or extra flag prints usage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        work = _make_repo(tmpdir)
        head = _git(work, "rev-parse", "HEAD")

        for args in (("build",), ("patch", "--force"), ()):
            result = _bump(work, *args)
            _assert_refused(work, result, head)
            assert "Usage" in result.stderr
    print("✓ Bump refuses invalid arguments test passed")


if __name__ == "__main__":
    print("Running bump_version tests...\n")

    test_bump_patch_commits_and_tags()
    test_bump_minor_and_major_reset_lower_parts()
    test_bump_with_push_sends_branch_and_tag()
    test_bump_refuses_unclean_tree()
    test_bump_refuses_other_branch()
    test_bump_refuses_unpushed_commit()
    test_bump_refuses_existing_tag()
    test_bump_refuses_invalid_arguments()

    print("\n✓ All bump_version tests passed!")
