"""Timestamped backup before overwrite."""

import shutil
from datetime import datetime
from pathlib import Path


def backup_files(project_dir, files_to_update):
    """Create timestamped backup of files that will be updated.

    Args:
        project_dir: Path to the project root
        files_to_update: list of relative output paths that will be overwritten

    Returns:
        Path to the backup directory, or None if no files were backed up
    """
    project_path = Path(project_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = project_path / ".djinit-backup" / timestamp

    backed_up = []
    for rel_path in files_to_update:
        src = project_path / rel_path
        if src.exists():
            dst = backup_dir / rel_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            backed_up.append(rel_path)

    if backed_up:
        print(f"Backed up {len(backed_up)} file(s) to {backup_dir}")
        return backup_dir

    return None
