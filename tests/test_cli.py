"""Tests for the CLI module."""

import getpass

import pytest

from djsuite.cli import build_parser, main, _valid_project_name


class TestProjectNameValidation:
    def test_valid_name(self):
        assert _valid_project_name("myproject") == "myproject"

    def test_hyphen_to_underscore(self):
        assert _valid_project_name("my-project") == "my_project"

    def test_invalid_name_raises(self):
        with pytest.raises(Exception):
            _valid_project_name("123invalid")

    def test_underscore_name(self):
        assert _valid_project_name("my_project") == "my_project"


class TestBuildParser:
    def test_version_flag(self, capsys):
        parser = build_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--version"])
        assert exc_info.value.code == 0

    def test_create_mode_defaults(self):
        parser = build_parser()
        args = parser.parse_args(["testproject"])
        assert args.project_name == "testproject"
        assert args.python_version == "3.12"
        assert args.django_version == "5.2"
        assert args.drf_version == "3.16"
        assert args.author == getpass.getuser()
        assert args.description == ""
        assert args.output_dir == "."
        assert not args.dry_run
        assert args.platform == "aws-eb"

    def test_create_mode_custom_flags(self):
        parser = build_parser()
        args = parser.parse_args([
            "myapp",
            "--python-version", "3.13",
            "--django-version", "5.3",
            "--drf-version", "3.17",
            "--author", "Nao Intelligence",
            "--description", "My API",
            "--output-dir", "/tmp",
            "--dry-run",
            "--platform", "aws-eb",
        ])
        assert args.project_name == "myapp"
        assert args.python_version == "3.13"
        assert args.django_version == "5.3"
        assert args.drf_version == "3.17"
        assert args.author == "Nao Intelligence"
        assert args.description == "My API"
        assert args.output_dir == "/tmp"
        assert args.dry_run
        assert args.platform == "aws-eb"

    def test_update_flags(self):
        parser = build_parser()
        args = parser.parse_args(["--update-ci", "--project-dir", "/path/to/project"])
        assert args.update_ci
        assert not args.update_docker
        assert not args.update_infra
        assert not args.update_all
        assert args.project_dir == "/path/to/project"

    def test_update_all_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--update-all", "--no-backup"])
        assert args.update_all
        assert args.no_backup

    def test_hyphenated_project_name_conversion(self):
        parser = build_parser()
        args = parser.parse_args(["my-cool-project"])
        assert args.project_name == "my_cool_project"


class TestMainFunction:
    def test_list_files(self, capsys):
        result = main(["--list-files"])
        assert result == 0
        captured = capsys.readouterr()
        assert ".env" in captured.out
        assert "main/settings.py" in captured.out

    def test_dry_run(self, tmp_path, capsys):
        result = main(["testproject", "--dry-run", "--output-dir", str(tmp_path)])
        assert result == 0
        captured = capsys.readouterr()
        assert "Would create project" in captured.out
        # Nothing actually created
        assert not (tmp_path / "testproject").exists()

    def test_missing_project_name(self):
        """Without project_name and no update flags, should error."""
        with pytest.raises(SystemExit):
            main([])
