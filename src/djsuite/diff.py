"""Diff summary display for update operations."""

import difflib
from pathlib import Path


def diff_summary(project_dir, output_path, new_content):
    """Show a summary of changes for a single file.

    Returns a status string: [NEW], [UNCHANGED], or [CHANGED] (+N/-M lines)
    """
    full_path = Path(project_dir) / output_path

    if not full_path.exists():
        return "[NEW]"

    old_content = full_path.read_text(encoding="utf-8")

    if old_content == new_content:
        return "[UNCHANGED]"

    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)

    diff = list(difflib.unified_diff(old_lines, new_lines, lineterm=""))

    added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

    return f"[CHANGED] (+{added}/-{removed} lines)"
