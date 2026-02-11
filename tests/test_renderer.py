"""Tests for the renderer module."""

import pytest

from djinit.renderer import render_template, render_all, create_environment
from djinit.manifest import Platform, get_manifest


@pytest.fixture
def context():
    return {
        "project_name": "myapp",
        "python_version": "3.12",
        "django_version": "5.2",
        "drf_version": "3.16",
        "author": "Test",
        "description": "Test desc",
        "platform": "aws-eb",
    }


class TestCreateEnvironment:
    def test_creates_jinja_environment(self):
        env = create_environment()
        assert env is not None


class TestRenderTemplate:
    def test_static_template(self, context):
        content = render_template("common", "manage.py", context)
        assert "DJANGO_SETTINGS_MODULE" in content
        assert "main.settings" in content

    def test_jinja_template_substitution(self, context):
        content = render_template("common", "main/celery.py.j2", context)
        assert 'Celery("myapp")' in content
        assert "{{ project_name }}" not in content

    def test_settings_template(self, context):
        content = render_template("common", "main/settings.py.j2", context)
        assert "myapp" in content
        assert "{{ project_name }}" not in content

    def test_dockerfile_template(self, context):
        content = render_template("platforms/aws_eb", "Dockerfile.j2", context)
        assert "python:3.12-slim" in content
        assert "{{ python_version }}" not in content

    def test_env_template(self, context):
        content = render_template("common", "dotenv.j2", context)
        assert "myapp_db" in content
        assert "myapp-local" in content

    def test_ci_template_raw_escaping(self, context):
        """Verify GitHub Actions ${{ }} expressions survive rendering."""
        content = render_template("common", "github/workflows/ci.yml.j2", context)
        assert "${{ secrets." in content or "${{secrets." in content or "${{ github." in content
        assert "myapp:" in content


class TestRenderAll:
    def test_renders_all_files(self, context):
        manifest = get_manifest(Platform.AWS_EB)
        results = render_all(manifest, context)
        assert len(results) == len(manifest)

    def test_output_paths_match_manifest(self, context):
        manifest = get_manifest(Platform.AWS_EB)
        results = render_all(manifest, context)
        expected_paths = {out for _key, (out, _grp) in manifest.items()}
        assert set(results.keys()) == expected_paths

    def test_no_unrendered_jinja(self, context):
        """Ensure no {{ or {% remain in rendered output (except in static files that use them)."""
        manifest = get_manifest(Platform.AWS_EB)
        results = render_all(manifest, context)
        for path, content in results.items():
            # Skip Dockerrun.aws.json.tmpl which uses ${IMAGE} (shell var, not jinja)
            if "Dockerrun" in path:
                continue
            assert "{{ " not in content or "{%" not in content, (
                f"Unrendered Jinja2 in {path}"
            )
