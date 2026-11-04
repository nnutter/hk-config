"""Check that the repository names exactly one hk version.

Every file that names an hk release must move together: a file left behind
builds its Pkl types from the older release, and hk rejects a config that
mixes two versions. `scripts/update-hk` does the move, so this test is the
check that the move reached every file.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# The schema pin, which is the version the whole repository targets.
PINNED = re.compile(
    r'^amends "package://github\.com/jdx/hk/releases/download/v(?P<version>[^/]+)/hk@.*$',
    re.MULTILINE,
)
# An hk release path, which a Pkl import and the tool pin both name.
DOWNLOAD = re.compile(r"jdx/hk/releases/download/v(?P<version>[^/]+)/")
TOOL = re.compile(r'^hk = "(?P<version>[^"]+)"', re.MULTILINE)


def hk_versions() -> dict[str, set[str]]:
    """Every hk version a tracked file names, by file."""
    names = subprocess.run(
        ["git", "ls-files", "*.pkl", "mise.toml"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()
    versions: dict[str, set[str]] = {}
    for name in names:
        text = (REPO / name).read_text()
        found = set(DOWNLOAD.findall(text)) | set(TOOL.findall(text))
        if found:
            versions[name] = found
    return versions


def test_every_hk_reference_names_the_pinned_version() -> None:
    """A file left at the old version makes hk reject the config."""
    match = PINNED.search((REPO / "Config.pkl").read_text())
    assert match is not None, "Config.pkl has no hk schema pin"
    pinned = match["version"]

    stale = {
        name: sorted(versions)
        for name, versions in hk_versions().items()
        if versions != {pinned}
    }
    assert not stale, f"Config.pkl pins hk {pinned}; these name another: {stale}"
