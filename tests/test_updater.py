"""Tests for the updater module."""

import json

import pytest

from djsuite.generator import generate
from djsuite.manifest import UpdateGroup
from djsuite.updater import run_update


@pytest.fixture
def context():
    return {
        "project_name": "testproject",
        "python_version": "3.12",
        "django_version": "5.2",
        "drf_version": "3.16",
        "author": "Test Author",
        "description": "A test project",
        "platform": "aws-eb",
    }


@pytest.fixture
def generated_project(tmp_path, context):
    generate(context, str(tmp_path))
    return tmp_path / "testproject"


class TestRunUpdate:
    def test_update_ci_files(self, generated_project, capsys):
        # Modify a CI file to trigger change
        ci_path = generated_project / ".github" / "workflows" / "ci.yml"
        ci_path.write_text("# modified\n")

        result = run_update(
            str(generated_project),
            groups={UpdateGroup.CI},
            no_backup=True,
        )
        assert result == 0
        captured = capsys.readouterr()
        assert "[CHANGED]" in captured.out

        # File should be restored to template content
        content = ci_path.read_text()
        assert "testproject" in content

    def test_update_unchanged_files(self, generated_project, capsys):
        result = run_update(
            str(generated_project),
            groups={UpdateGroup.CI},
            no_backup=True,
        )
        assert result == 0
        captured = capsys.readouterr()
        assert "up to date" in captured.out

    def test_update_creates_backup(self, generated_project, capsys):
        # Modify a file to trigger backup
        ci_path = generated_project / ".github" / "workflows" / "ci.yml"
        ci_path.write_text("# modified\n")

        result = run_update(
            str(generated_project),
            groups={UpdateGroup.CI},
            no_backup=False,
        )
        assert result == 0
        backup_dir = generated_project / ".djsuite-backup"
        assert backup_dir.exists()

    def test_update_no_backup_flag(self, generated_project, capsys):
        ci_path = generated_project / ".github" / "workflows" / "ci.yml"
        ci_path.write_text("# modified\n")

        run_update(
            str(generated_project),
            groups={UpdateGroup.CI},
            no_backup=True,
        )
        backup_dir = generated_project / ".djsuite-backup"
        assert not backup_dir.exists()

    def test_update_docker_files(self, generated_project, capsys):
        dockerfile = generated_project / "Dockerfile"
        dockerfile.write_text("# old\n")

        result = run_update(
            str(generated_project),
            groups={UpdateGroup.DOCKER},
            no_backup=True,
        )
        assert result == 0
        content = dockerfile.read_text()
        assert "python:3.12-slim" in content

    def test_update_infra_files(self, generated_project, capsys):
        result = run_update(
            str(generated_project),
            groups={UpdateGroup.INFRA},
            no_backup=True,
        )
        assert result == 0

    def test_error_without_djsuite_json(self, tmp_path, capsys):
        (tmp_path / "noproject").mkdir()
        result = run_update(
            str(tmp_path / "noproject"),
            groups={UpdateGroup.CI},
        )
        assert result == 1
        captured = capsys.readouterr()
        assert ".djsuite.json" in captured.out

    def test_update_all_groups(self, generated_project, capsys):
        # Modify files in multiple groups
        (generated_project / "Dockerfile").write_text("# old\n")
        (generated_project / ".github" / "workflows" / "ci.yml").write_text("# old\n")

        result = run_update(
            str(generated_project),
            groups={
                UpdateGroup.CI,
                UpdateGroup.DOCKER,
                UpdateGroup.INFRA,
                UpdateGroup.ROOT,
            },
            no_backup=True,
        )
        assert result == 0
        captured = capsys.readouterr()
        assert "Updated" in captured.out

    def test_new_file_shown(self, generated_project, capsys):
        # Remove a file so it shows as [NEW]
        (generated_project / ".github" / "copilot-instructions.md").unlink()

        result = run_update(
            str(generated_project),
            groups={UpdateGroup.CI},
            no_backup=True,
        )
        assert result == 0
        captured = capsys.readouterr()
        assert "[NEW]" in captured.out

    def test_backwards_compat_no_platform_key(self, generated_project, capsys):
        """Existing projects without 'platform' in .djsuite.json default to aws-eb."""
        config_path = generated_project / ".djsuite.json"
        config = json.loads(config_path.read_text())
        del config["platform"]
        config_path.write_text(json.dumps(config, indent=2) + "\n")

        ci_path = generated_project / ".github" / "workflows" / "ci.yml"
        ci_path.write_text("# modified\n")

        result = run_update(
            str(generated_project),
            groups={UpdateGroup.CI},
            no_backup=True,
        )
        assert result == 0
        content = ci_path.read_text()
        assert "testproject" in content
