"""Check the packaged Pkl package the way a consumer resolves it.

Pkl fetches the package's metadata file (name@version, no extension) first,
follows the packageZipUrl it lists, and then loads modules out of that zip.
Serving a release-style tree over HTTP reproduces that chain, so a missing
asset or a broken import fails here rather than after the release is published.
"""

from __future__ import annotations

import functools
import http.server
import shutil
import subprocess
import threading
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent

# Pkl asks for the package on one host and for the zip it names on another, so
# the checks redirect both at the local server.
PACKAGE_HOST = "hk-config.test"
GITHUB_RELEASE = "https://github.com/nnutter/hk-config/releases/download/"

# One entry per builtin: the Pkl expression for the command a consumer must end
# up with, and that command. String commands and Command objects read back
# differently, so each entry spells out its own expression.
BUILTINS = {
    "mdlint": (
        'steps["mdlint"].check.command',
        "mdlint format --check {{files}} && mdlint check --no-fix {{files}}",
    ),
    "go_check_sumtype": (
        'steps["go_check_sumtype"].check.command.argv.join(" ")',
        "go-check-sumtype -default-signifies-exhaustive=false -include-shared-interfaces ./...",
    ),
    "constable": (
        'steps["constable"].fix.command.argv.join(" ")',
        "constable -fix ./...",
    ),
    "gohawk": (
        'steps["gohawk"].check.command.argv.join(" ")',
        "gohawk ./...",
    ),
    "nilaway": (
        'steps["nilaway"].check.command',
        "nilaway -include-pkgs $(go list -m) ./...",
    ),
    "testifylint": (
        'steps["testifylint"].check.command.argv.join(" ")',
        "testifylint ./...",
    ),
    "timber_commit_msg": (
        'steps["timber_commit_msg"].fix.command.argv.join(" ")',
        "timber review commit-msg {{commit_msg_file}}",
    ),
}


class Package:
    """The packaged artifacts, named the way a consumer names them."""

    def __init__(self, dist: Path) -> None:
        self.zip = min(dist.glob("*.zip"))
        self.name, _, self.version = self.zip.stem.partition("@")
        self.metadata = dist / self.zip.stem
        assert self.version, f"unexpected package name: {self.zip.name}"
        assert self.metadata.is_file(), f"no metadata file next to {self.zip.name}"
        with zipfile.ZipFile(self.zip) as archive:
            self.modules = archive.namelist()
        assert {"Builtins.pkl", "Config.pkl"} <= set(self.modules), self.modules


@pytest.fixture(scope="session")
def package(tmp_path_factory: pytest.TempPathFactory) -> Package:
    """Build the package, so the test never asserts on a stale artifact."""
    dist = tmp_path_factory.mktemp("dist")
    subprocess.run(
        ["pkl", "project", "package", "--output-path", str(dist)],
        cwd=REPO,
        check=True,
    )
    return Package(dist)


@pytest.fixture(scope="session")
def release(package: Package, tmp_path_factory: pytest.TempPathFactory):
    """Serve the package in the layout a GitHub release uses."""
    root = tmp_path_factory.mktemp("release")
    (root / f"v{package.version}").mkdir()
    shutil.copy(package.metadata, root / package.metadata.name)
    shutil.copy(package.zip, root / f"v{package.version}" / package.zip.name)

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            pass

    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(Quiet, directory=str(root))
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/"
    finally:
        server.shutdown()
        server.server_close()


def pkl_eval(release: str, work: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "pkl",
            "eval",
            *args,
            # Ignore any cached copy so the packaged bytes are what is evaluated.
            "--no-cache",
            "--allowed-resources=.*",
            f"--http-rewrite=https://{PACKAGE_HOST}/={release}",
            f"--http-rewrite={GITHUB_RELEASE}={release}",
        ],
        cwd=work,
        check=False,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize(
    ("step", "expression", "expected_command"),
    [(name, *spec) for name, spec in BUILTINS.items()],
)
def test_consumer_resolves_builtin(
    package: Package,
    release: str,
    tmp_path: Path,
    step: str,
    expression: str,
    expected_command: str,
) -> None:
    """A consumer amends Config.pkl and assigns the builtin as a step.

    The step goes into `steps` only to read its command back; a commit-message
    step belongs in another hook, which this test does not exercise.
    """
    uri = f"package://{PACKAGE_HOST}/{package.name}@{package.version}"
    consumer = tmp_path / "hk.pkl"
    consumer.write_text(
        f'''amends "{uri}#/Config.pkl"

import "{uri}#/Builtins.pkl" as Extra

steps {{
  ["{step}"] = Extra.{step}
}}
'''
    )
    result = pkl_eval(release, tmp_path, str(consumer), "-x", expression)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == expected_command
