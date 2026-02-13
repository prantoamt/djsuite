"""New project generation."""

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

from djsuite.manifest import get_manifest
from djsuite.renderer import render_all


def generate(context, output_dir=".", platform=None):
    """Generate a new Django project."""
    from djsuite.manifest import Platform
    if platform is None:
        platform = Platform.AWS_EB

    project_name = context["project_name"]
    project_path = Path(output_dir) / project_name

    if project_path.exists():
        print(f"Error: directory {project_path} already exists")
        return 1

    manifest = get_manifest(platform)
    rendered = render_all(manifest, context)

    for output_path, content in sorted(rendered.items()):
        full_path = project_path / output_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        # Set executable bit on .sh files
        if output_path.endswith(".sh"):
            full_path.chmod(full_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print(f"  created {output_path}")

    # Write .djsuite.json config file
    config = {
        "djsuite_version": "0.1.0",
        "platform": platform.value,
        **context,
    }
    config_path = project_path / ".djsuite.json"
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(f"  created .djsuite.json")

    # Run pdm lock to pin dependency versions
    if shutil.which("pdm"):
        print("\nRunning pdm lock to pin dependencies...")
        result = subprocess.run(
            ["pdm", "lock"],
            cwd=project_path,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("  pdm.lock created")
        else:
            print(f"  pdm lock failed (you can run it manually): {result.stderr.strip()}")
    else:
        print("\nNote: pdm not found — run 'pdm lock' after installing PDM to pin dependencies.")

    print(f"\nProject {project_name} created at {project_path.resolve()}")
    print(f"\nNext steps:")
    print(f"  cd {project_name}")
    print(f"  pdm install")
    print(f"  cp .env .env.local  # edit with your settings")
    print(f"  pdm run migrate")
    print(f"  pdm run startdev 8000")
    return 0


def dry_run(context, output_dir=".", platform=None):
    """Show what files would be generated without writing anything."""
    from djsuite.manifest import Platform
    if platform is None:
        platform = Platform.AWS_EB

    project_name = context["project_name"]
    project_path = Path(output_dir) / project_name

    manifest = get_manifest(platform)

    print(f"Would create project at: {project_path.resolve()}\n")
    print(f"Files that would be generated:")

    for _key, (output_path, _group) in sorted(manifest.items(), key=lambda item: item[1][0]):
        print(f"  {output_path}")

    print(f"  .djsuite.json")
    print(f"\nTotal: {len(manifest) + 1} files")
    return 0
