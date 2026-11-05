"""Check the hook templates under the hk binary that consumers run.

Pkl 0.32 accepts syntax that the Pkl evaluator embedded in hk rejects, so a
template that evaluates in the package tests can still fail to load in hk.
This test loads the working tree's Hooks.pkl with hk itself.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HK = shutil.which("hk")

# The schema pin names the hk release this package targets, and the consumer
# config has to amend the same one.
PINNED = re.compile(
    r'^amends "package://github\.com/jdx/hk/releases/download/v(?P<version>[^/]+)/hk@.*$',
    re.MULTILINE,
)

GROUPS = [
    "agentskills",
    "buf",
    "go",
    "json",
    "proto",
    "python",
    "rust",
    "shell",
    "toml",
    "ts-backend",
    "ts-frontend",
    "yaml",
]

pytestmark = pytest.mark.skipif(HK is None, reason="hk is not installed")


def validate(work: Path, groups: str) -> subprocess.CompletedProcess[str]:
    """Validate a consumer config that imports the working tree's Hooks.pkl."""
    assert HK is not None, "hk is not installed"
    match = PINNED.search((REPO / "Config.pkl").read_text())
    assert match is not None, "Config.pkl has no hk schema pin"
    version = match["version"]
    (work / "hk.pkl").write_text(
        f'''amends "package://github.com/jdx/hk/releases/download/v{version}/hk@{version}#/Config.pkl"

import "{REPO}/Hooks.pkl" as Hooks

hooks = Hooks.all({groups})
'''
    )
    return subprocess.run(
        [HK, "validate"],
        cwd=work,
        check=False,
        capture_output=True,
        text=True,
    )


def test_every_group_loads(tmp_path: Path) -> None:
    """hk evaluates the module, the hook defaults, and every group's steps."""
    groups = "List(" + ", ".join(f'"{name}"' for name in GROUPS) + ")"
    result = validate(tmp_path, groups)
    assert result.returncode == 0, result.stdout + result.stderr


def test_defaults_alone_load(tmp_path: Path) -> None:
    """A consumer that names no groups still gets a valid config."""
    result = validate(tmp_path, "List()")
    assert result.returncode == 0, result.stdout + result.stderr


def test_unknown_group_fails(tmp_path: Path) -> None:
    """hk reports the group names instead of running a config with no steps."""
    result = validate(tmp_path, 'List("nope")')
    assert result.returncode != 0
    assert "is not a group" in result.stdout + result.stderr
