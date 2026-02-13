"""File manifest mapping template paths to output paths and update groups."""

from enum import Enum


class UpdateGroup(Enum):
    CI = "ci"
    DOCKER = "docker"
    INFRA = "infra"
    ROOT = "root"
    APP_MAIN = "app_main"
    APP_BASE = "app_base"


class Platform(Enum):
    AWS_EB = "aws-eb"

    @classmethod
    def from_str(cls, value):
        """Convert a string to a Platform enum member."""
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"Unknown platform: {value!r}. Choose from: {[m.value for m in cls]}")


# Mapping: template_path -> (output_path, UpdateGroup)
# Template path is relative to the templates/<dir_prefix>/ directory.
# Output path is relative to the project root.

COMMON_MANIFEST = {
    # Root files
    "dotenv.j2": (".env", UpdateGroup.ROOT),
    "gitignore": (".gitignore", UpdateGroup.ROOT),
    "README.md.j2": ("README.md", UpdateGroup.ROOT),
    "CONTRIBUTING.md.j2": ("CONTRIBUTING.md", UpdateGroup.ROOT),
    "CHANGELOG.md": ("CHANGELOG.md", UpdateGroup.ROOT),
    "pyproject.toml.j2": ("pyproject.toml", UpdateGroup.ROOT),
    "docker-compose.yml.j2": ("docker-compose.yml", UpdateGroup.ROOT),
    "pre-commit-config.yaml": (".pre-commit-config.yaml", UpdateGroup.ROOT),
    "manage.py": ("manage.py", UpdateGroup.ROOT),
    "conftest.py.j2": ("conftest.py", UpdateGroup.ROOT),

    # CI (.github/)
    "github/copilot-instructions.md.j2": (".github/copilot-instructions.md", UpdateGroup.CI),
    "github/PULL_REQUEST_TEMPLATE.md": (".github/PULL_REQUEST_TEMPLATE.md", UpdateGroup.CI),
    "github/release.yml": (".github/release.yml", UpdateGroup.CI),
    "github/workflows/ci.yml.j2": (".github/workflows/ci.yml", UpdateGroup.CI),
    "github/workflows/auto-label.yml": (".github/workflows/auto-label.yml", UpdateGroup.CI),

    # main/ app
    "main/__init__.py": ("main/__init__.py", UpdateGroup.APP_MAIN),
    "main/apps.py": ("main/apps.py", UpdateGroup.APP_MAIN),
    "main/asgi.py": ("main/asgi.py", UpdateGroup.APP_MAIN),
    "main/celery.py.j2": ("main/celery.py", UpdateGroup.APP_MAIN),
    "main/settings.py.j2": ("main/settings.py", UpdateGroup.APP_MAIN),
    "main/urls.py": ("main/urls.py", UpdateGroup.APP_MAIN),
    "main/wsgi.py": ("main/wsgi.py", UpdateGroup.APP_MAIN),

    # base/ app
    "base/__init__.py": ("base/__init__.py", UpdateGroup.APP_BASE),
    "base/apps.py": ("base/apps.py", UpdateGroup.APP_BASE),
    "base/containers.py": ("base/containers.py", UpdateGroup.APP_BASE),
    "base/models.py": ("base/models.py", UpdateGroup.APP_BASE),
    "base/pagination.py": ("base/pagination.py", UpdateGroup.APP_BASE),
    "base/urls.py": ("base/urls.py", UpdateGroup.APP_BASE),
    "base/views.py": ("base/views.py", UpdateGroup.APP_BASE),
    "base/constants/__init__.py": ("base/constants/__init__.py", UpdateGroup.APP_BASE),
    "base/constants/celery_task_status.py": ("base/constants/celery_task_status.py", UpdateGroup.APP_BASE),
    "base/constants/magic_numbers.py": ("base/constants/magic_numbers.py", UpdateGroup.APP_BASE),
    "base/constants/model_viewset.py": ("base/constants/model_viewset.py", UpdateGroup.APP_BASE),
    "base/management/commands/createsu.py": ("base/management/commands/createsu.py", UpdateGroup.APP_BASE),
    "base/migrations/__init__.py": ("base/migrations/__init__.py", UpdateGroup.APP_BASE),
    "base/services/__init__.py": ("base/services/__init__.py", UpdateGroup.APP_BASE),
    "base/services/orphan_service.py": ("base/services/orphan_service.py", UpdateGroup.APP_BASE),
    "base/tests/__init__.py": ("base/tests/__init__.py", UpdateGroup.APP_BASE),
}

PLATFORM_MANIFESTS = {
    Platform.AWS_EB: {
        # Docker
        "Dockerfile.j2": ("Dockerfile", UpdateGroup.DOCKER),
        "entrypoint.sh": ("entrypoint.sh", UpdateGroup.DOCKER),
        "release.sh": ("release.sh", UpdateGroup.DOCKER),
        "supervisord_app.conf": ("supervisord_app.conf", UpdateGroup.DOCKER),
        "supervisord_worker_beat.conf": ("supervisord_worker_beat.conf", UpdateGroup.DOCKER),

        # CD (.github/)
        "github/workflows/dev-cd.yml.j2": (".github/workflows/dev-cd.yml", UpdateGroup.CI),
        "github/workflows/prod-cd.yml.j2": (".github/workflows/prod-cd.yml", UpdateGroup.CI),

        # Platform (.platform/)
        "platform/hooks/postdeploy/01_release.sh": (".platform/hooks/postdeploy/01_release.sh", UpdateGroup.INFRA),
        "platform/hooks/postdeploy/02_setup_log_whisperer.sh": (".platform/hooks/postdeploy/02_setup_log_whisperer.sh", UpdateGroup.INFRA),
        "platform/hooks/predeploy/01_cleanup_log_whisperer_cron.sh": (".platform/hooks/predeploy/01_cleanup_log_whisperer_cron.sh", UpdateGroup.INFRA),

        # Infra
        "infra/Dockerrun.aws.json.tmpl": ("infra/Dockerrun.aws.json.tmpl", UpdateGroup.INFRA),

        # Nginx
        "nginx/celery.conf": ("nginx/celery.conf", UpdateGroup.INFRA),
        "nginx/default.conf": ("nginx/default.conf", UpdateGroup.INFRA),
    },
}


def get_manifest(platform):
    """Merge common and platform-specific manifests into a single dict.

    Keys are (dir_prefix, template_path) tuples so the renderer knows
    which subdirectory to load from.

    Returns:
        dict of (dir_prefix, template_path) -> (output_path, UpdateGroup)
    """
    merged = {}
    for tpl, value in COMMON_MANIFEST.items():
        merged[("common", tpl)] = value
    platform_manifest = PLATFORM_MANIFESTS.get(platform, {})
    dir_prefix = f"platforms/{platform.value.replace('-', '_')}"
    for tpl, value in platform_manifest.items():
        merged[(dir_prefix, tpl)] = value
    return merged


def files_for_groups(groups, platform):
    """Return manifest entries for the given set of UpdateGroups."""
    manifest = get_manifest(platform)
    return {
        key: (out, grp)
        for key, (out, grp) in manifest.items()
        if grp in groups
    }


def all_output_paths(platform):
    """Return all output paths in order."""
    manifest = get_manifest(platform)
    return [out for _key, (out, _grp) in sorted(manifest.items(), key=lambda item: item[1][0])]
