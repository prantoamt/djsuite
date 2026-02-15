"""Selective update of files in existing projects."""

import json
import stat
from pathlib import Path

from djsuite.backup import backup_files
from djsuite.diff import diff_summary
from djsuite.manifest import Platform, files_for_groups
from djsuite.renderer import render_all


def _load_context(project_dir):
    """Load project context and platform from .djsuite.json.

    Returns:
        (context_dict, Platform) tuple, or (None, None) on error.
    """
    config_path = Path(project_dir) / ".djsuite.json"
    if not config_path.exists():
        print(f"Error: {config_path} not found. Is this a djsuite project?")
        print("Run 'djsuite <project_name>' first to create a project.")
        return None, None

    with open(config_path) as f:
        config = json.load(f)

    # Extract context keys
    context_keys = [
        "project_name",
        "python_version",
        "django_version",
        "drf_version",
        "author",
        "description",
    ]
    context = {k: config.get(k, "") for k in context_keys}

    # Read platform, defaulting to aws-eb for backwards compatibility
    platform_str = config.get("platform", "aws-eb")
    platform = Platform.from_str(platform_str)
    context["platform"] = platform.value

    return context, platform


def run_update(project_dir, groups, no_backup=False):
    """Update files in an existing project.

    Args:
        project_dir: Path to the project root
        groups: set of UpdateGroup values to update
        no_backup: if True, skip backup
    """
    context, platform = _load_context(project_dir)
    if context is None:
        return 1

    manifest = files_for_groups(groups, platform)
    if not manifest:
        print("No files to update for the selected groups.")
        return 0

    rendered = render_all(manifest, context)

    # Show diff summary
    print(f"Updating {len(rendered)} file(s) in {Path(project_dir).resolve()}:\n")
    statuses = {}
    for output_path, content in sorted(rendered.items()):
        status = diff_summary(project_dir, output_path, content)
        statuses[output_path] = status
        print(f"  {status:30s} {output_path}")

    # Filter out unchanged files
    files_to_write = {path: content for path, content in rendered.items() if statuses[path] != "[UNCHANGED]"}

    if not files_to_write:
        print("\nAll files are up to date.")
        return 0

    # Backup
    if not no_backup:
        backup_files(project_dir, list(files_to_write.keys()))

    # Write files
    project_path = Path(project_dir)
    for output_path, content in sorted(files_to_write.items()):
        full_path = project_path / output_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        if output_path.endswith(".sh"):
            full_path.chmod(full_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    print(f"\nUpdated {len(files_to_write)} file(s).")
    return 0
