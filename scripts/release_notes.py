"""Check release metadata and print the CHANGELOG notes for a version.

Usage:
    python scripts/release_notes.py            # check plugin.json version is in CHANGELOG
    python scripts/release_notes.py v1.2.0     # also check the tag matches, print its notes

Exits non-zero when the tag, plugin.json and CHANGELOG.md disagree.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_JSON = REPO_ROOT / "plugins" / "basedpyright-lsp" / ".claude-plugin" / "plugin.json"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"


def changelog_section(version: str) -> str | None:
    text = CHANGELOG.read_text(encoding="utf-8")
    match = re.search(
        rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|^\[[^\]]+\]: |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match else None


def main() -> None:
    version = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))["version"]

    if len(sys.argv) > 1 and sys.argv[1] != f"v{version}":
        sys.exit(f"Tag {sys.argv[1]} does not match plugin.json version {version}")

    notes = changelog_section(version)
    if not notes:
        sys.exit(f"CHANGELOG.md has no entry for version {version}")

    if len(sys.argv) > 1:
        print(notes)
    else:
        print(f"plugin.json version {version} has a CHANGELOG entry")


if __name__ == "__main__":
    main()
