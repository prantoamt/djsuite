"""Tests for the generator module."""

import json
import stat

import pytest

from djsuite.generator import dry_run, generate


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


class TestGenerate:
    def test_creates_project_directory(self, tmp_path, context):
        generate(context, str(tmp_path))
        project_dir = tmp_path / "testproject"
        assert project_dir.exists()
        assert project_dir.is_dir()

    def test_creates_djsuite_json(self, tmp_path, context):
        generate(context, str(tmp_path))
        config_path = tmp_path / "testproject" / ".djsuite.json"
        assert config_path.exists()
        config = json.loads(config_path.read_text())
        assert config["project_name"] == "testproject"
        assert config["python_version"] == "3.12"
        assert config["djsuite_version"] == "0.1.0"
        assert config["platform"] == "aws-eb"

    def test_creates_key_files(self, tmp_path, context):
        generate(context, str(tmp_path))
        project_dir = tmp_path / "testproject"
        assert (project_dir / "manage.py").exists()
        assert (project_dir / ".env").exists()
        assert (project_dir / ".gitignore").exists()
        assert (project_dir / "pyproject.toml").exists()
        assert (project_dir / "Dockerfile").exists()
        assert (project_dir / "main" / "settings.py").exists()
        assert (project_dir / "main" / "celery.py").exists()
        assert (project_dir / "base" / "models.py").exists()
        assert (project_dir / "base" / "views.py").exists()
        assert (project_dir / "CONTRIBUTING.md").exists()
        assert (project_dir / "CHANGELOG.md").exists()
        assert (project_dir / "docker-compose.yml").exists()
        assert (project_dir / ".pre-commit-config.yaml").exists()

    def test_creates_github_workflows(self, tmp_path, context):
        generate(context, str(tmp_path))
        project_dir = tmp_path / "testproject"
        assert (project_dir / ".github" / "workflows" / "ci.yml").exists()
        assert (project_dir / ".github" / "workflows" / "dev-cd.yml").exists()
        assert (project_dir / ".github" / "workflows" / "prod-cd.yml").exists()
        assert (project_dir / ".github" / "workflows" / "auto-label.yml").exists()
        assert (project_dir / ".github" / "copilot-instructions.md").exists()
        assert (project_dir / ".github" / "release.yml").exists()
        assert (project_dir / ".github" / "PULL_REQUEST_TEMPLATE.md").exists()

    def test_creates_platform_hooks(self, tmp_path, context):
        generate(context, str(tmp_path))
        project_dir = tmp_path / "testproject"
        assert (project_dir / ".platform" / "hooks" / "postdeploy" / "01_release.sh").exists()
        assert (project_dir / ".platform" / "hooks" / "predeploy" / "01_cleanup_log_whisperer_cron.sh").exists()

    def test_template_substitution_settings(self, tmp_path, context):
        generate(context, str(tmp_path))
        settings = (tmp_path / "testproject" / "main" / "settings.py").read_text()
        assert "testproject" in settings
        assert "comvado" not in settings.lower()
        assert 'CELERY_TIMEZONE = "UTC"' in settings

    def test_template_substitution_celery(self, tmp_path, context):
        generate(context, str(tmp_path))
        celery_py = (tmp_path / "testproject" / "main" / "celery.py").read_text()
        assert 'Celery("testproject")' in celery_py

    def test_template_substitution_pyproject(self, tmp_path, context):
        generate(context, str(tmp_path))
        pyproject = (tmp_path / "testproject" / "pyproject.toml").read_text()
        assert 'name = "testproject"' in pyproject
        assert 'name = "Test Author"' in pyproject
        assert 'description = "A test project"' in pyproject
        assert "==3.12.*" in pyproject
        assert "Django==5.2.*" in pyproject
        assert "djangorestframework==3.16.*" in pyproject

    def test_template_substitution_env(self, tmp_path, context):
        generate(context, str(tmp_path))
        env_file = (tmp_path / "testproject" / ".env").read_text()
        assert "testproject_db" in env_file
        assert "testproject-local" in env_file

    def test_template_substitution_dockerfile(self, tmp_path, context):
        generate(context, str(tmp_path))
        dockerfile = (tmp_path / "testproject" / "Dockerfile").read_text()
        assert "python:3.12-slim" in dockerfile
        assert "company-auth" not in dockerfile

    def test_dockerfile_runs_as_non_root(self, tmp_path, context):
        generate(context, str(tmp_path))
        dockerfile = (tmp_path / "testproject" / "Dockerfile").read_text()
        assert "USER appuser" in dockerfile

    def test_settings_security_headers(self, tmp_path, context):
        generate(context, str(tmp_path))
        settings = (tmp_path / "testproject" / "main" / "settings.py").read_text()
        assert "SECURE_HSTS_SECONDS" in settings
        assert "SESSION_COOKIE_SECURE" in settings
        assert "CSRF_COOKIE_SECURE" in settings
        assert "CONN_MAX_AGE" in settings

    def test_health_check_endpoint(self, tmp_path, context):
        generate(context, str(tmp_path))
        views = (tmp_path / "testproject" / "base" / "views.py").read_text()
        urls = (tmp_path / "testproject" / "base" / "urls.py").read_text()
        assert "HealthCheckView" in views
        assert "health/" in urls

    def test_template_substitution_ci(self, tmp_path, context):
        generate(context, str(tmp_path))
        ci = (tmp_path / "testproject" / ".github" / "workflows" / "ci.yml").read_text()
        assert "testproject:" in ci
        assert "comvado" not in ci.lower()

    def test_template_substitution_contributing(self, tmp_path, context):
        generate(context, str(tmp_path))
        contributing = (tmp_path / "testproject" / "CONTRIBUTING.md").read_text()
        assert "testproject" in contributing
        assert "trunk-based" in contributing.lower()
        assert "feat" in contributing

    def test_template_substitution_cd(self, tmp_path, context):
        generate(context, str(tmp_path))
        dev_cd = (tmp_path / "testproject" / ".github" / "workflows" / "dev-cd.yml").read_text()
        assert "ECR_REPO: testproject" in dev_cd
        assert "testproject-${VERSION_LABEL}.zip" in dev_cd
        assert "comvado" not in dev_cd.lower()

    def test_cd_uses_git_tags_not_release_drafter(self, tmp_path, context):
        generate(context, str(tmp_path))
        project_dir = tmp_path / "testproject" / ".github" / "workflows"
        dev_cd = (project_dir / "dev-cd.yml").read_text()
        prod_cd = (project_dir / "prod-cd.yml").read_text()
        assert "release-drafter" not in dev_cd
        assert "release-drafter" not in prod_cd
        assert "git describe --tags" in dev_cd
        assert "gh release create" in dev_cd
        assert "CHANGELOG.md" in prod_cd

    def test_sh_files_are_executable(self, tmp_path, context):
        generate(context, str(tmp_path))
        project_dir = tmp_path / "testproject"
        entrypoint = project_dir / "entrypoint.sh"
        assert entrypoint.exists()
        mode = entrypoint.stat().st_mode
        assert mode & stat.S_IXUSR

    def test_no_project_specific_code_in_settings(self, tmp_path, context):
        generate(context, str(tmp_path))
        settings = (tmp_path / "testproject" / "main" / "settings.py").read_text()
        assert "allauth" not in settings
        assert "company_auth" not in settings
        assert "SOCIALACCOUNT" not in settings
        assert "phonenumber" not in settings
        assert "auditlog" not in settings
        assert "ADMIN_PORTAL_URL" not in settings
        assert "FRONTEND_URL" not in settings
        assert "EMAIL_BACKEND" not in settings

    def test_no_project_specific_deps_in_pyproject(self, tmp_path, context):
        generate(context, str(tmp_path))
        pyproject = (tmp_path / "testproject" / "pyproject.toml").read_text()
        assert "company-auth" not in pyproject
        assert "phonenumber" not in pyproject
        assert "xlsxwriter" not in pyproject
        assert "pdfplumber" not in pyproject
        assert "pytesseract" not in pyproject
        assert "numpy" not in pyproject
        assert "pandas" not in pyproject
        assert "auditlog" not in pyproject

    def test_urls_generalized(self, tmp_path, context):
        generate(context, str(tmp_path))
        urls = (tmp_path / "testproject" / "main" / "urls.py").read_text()
        assert "company_auth" not in urls
        assert "company_app" not in urls
        assert "mobilfunkt" not in urls
        assert "user.urls" not in urls
        assert "base.urls" in urls

    def test_error_if_dir_exists(self, tmp_path, context, capsys):
        (tmp_path / "testproject").mkdir()
        result = generate(context, str(tmp_path))
        assert result == 1
        captured = capsys.readouterr()
        assert "already exists" in captured.out


class TestDryRun:
    def test_shows_file_list(self, tmp_path, context, capsys):
        dry_run(context, str(tmp_path))
        captured = capsys.readouterr()
        assert "manage.py" in captured.out
        assert "main/settings.py" in captured.out
        assert ".djsuite.json" in captured.out
        assert "Total:" in captured.out

    def test_does_not_create_files(self, tmp_path, context):
        dry_run(context, str(tmp_path))
        assert not (tmp_path / "testproject").exists()
