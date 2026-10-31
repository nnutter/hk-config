"""Check that the packaged Pkl package resolves like a consumer's.

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


class Package:
    """The packaged artifacts, named the way a consumer names them."""

    def __init__(self, dist: Path) -> None:
        self.zip = sorted(dist.glob("*.zip"))[0]
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
        def log_message(self, *args: object) -> None:
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
        capture_output=True,
        text=True,
    )


def test_package_resolves(package: Package, release: str, tmp_path: Path) -> None:
    """The schema pin and the builtins module both load from the packaged zip."""
    uri = f"package://{PACKAGE_HOST}/{package.name}@{package.version}"
    for module in ("Config.pkl", "Builtins.pkl"):
        result = pkl_eval(release, tmp_path, f"{uri}#/{module}", "-f", "json")
        assert result.returncode == 0, f"{module}: {result.stderr}"
        assert result.stdout.strip(), f"{module} evaluated to nothing"
