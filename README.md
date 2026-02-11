<div align="center">

# djinit

**Production-ready Django project scaffolding in one command.**

Generates a fully-configured Django + DRF project with Docker, CI/CD,
Celery, PostgreSQL, and cloud deployment — so you ship features on day one,
not boilerplate.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![Django 5.x](https://img.shields.io/badge/django-5.x-092E20?logo=django&logoColor=white)](https://djangoproject.com)
[![License](https://img.shields.io/badge/license-proprietary-lightgrey)]()

</div>

---

## Why djinit?

Every new Django project at CFAI starts with the same stack: DRF, JWT auth,
Celery workers, PostgreSQL, S3 storage, Docker, GitHub Actions CI/CD, and
AWS Elastic Beanstalk deployment. Setting this up by hand takes hours and
inevitably drifts between projects.

**djinit solves this.** One command generates 44 files with a proven,
battle-tested structure — and when the template evolves, `--update-*` flags
push changes to existing projects without touching your custom code.

---

## Quick Start

### Install

```bash
pipx install git+https://github.com/Nao-Intelligence/djinit.git
```

### Create a project

```bash
djinit myproject --author "Nao Intelligence" --description "Payments API"
```

```
  created .env
  created .github/workflows/ci.yml
  created .github/workflows/dev-cd.yml
  created Dockerfile
  created main/settings.py
  created base/models.py
  ... (44 files total)

Project myproject created at /home/you/myproject

Next steps:
  cd myproject
  pdm install
  cp .env .env.local  # edit with your settings
  pdm run migrate
  pdm run startdev 8000
```

---

## What You Get

```
myproject/
├── .djinit.json                          # djinit metadata (version, platform, context)
├── .env                                  # Environment variables (local defaults)
├── .gitignore
├── .github/
│   ├── copilot-instructions.md           # AI assistant context for the project
│   └── workflows/
│       ├── ci.yml                        # Lint + test on every PR
│       ├── dev-cd.yml                    # Auto-deploy to dev on push to development
│       └── prod-cd.yml                   # Auto-deploy to prod on push to main
├── .platform/hooks/                      # Elastic Beanstalk lifecycle hooks
│   ├── postdeploy/
│   │   ├── 01_release.sh                # Run migrations + collectstatic
│   │   └── 02_setup_log_whisperer.sh    # Log anomaly monitoring
│   └── predeploy/
│       └── 01_cleanup_log_whisperer_cron.sh
├── Dockerfile                            # Multi-stage build (slim Python image)
├── README.md                             # Auto-generated project README
├── base/                                 # Shared utilities app
│   ├── constants/                        # Enums and magic numbers
│   ├── containers.py                     # Dependency injection (dependency-injector)
│   ├── management/commands/createsu.py   # Create superuser from env vars
│   ├── models.py                         # TimeStampMixin base model
│   ├── pagination.py                     # StandardResultsSetPagination
│   ├── services/orphan_service.py        # Orphan record cleanup
│   └── views.py                          # Celery task status endpoint
├── conftest.py                           # pytest configuration
├── entrypoint.sh                         # Docker entrypoint (role-based: web/worker/beat)
├── infra/Dockerrun.aws.json.tmpl         # EB Docker config template
├── main/                                 # Django project package
│   ├── celery.py                         # Celery app configuration
│   ├── settings.py                       # Full settings with env-based config
│   ├── urls.py                           # API routes + Swagger UI
│   └── wsgi.py / asgi.py
├── manage.py
├── nginx/                                # Nginx configs (web + worker roles)
├── pyproject.toml                        # PDM project with all dependencies
├── release.sh                            # Migration + static collection script
├── supervisord_app.conf                  # Supervisor: gunicorn + nginx
└── supervisord_worker_beat.conf          # Supervisor: celery worker + beat
```

### Stack at a Glance

| Layer | Technology |
|-------|-----------|
| **Framework** | Django 5.2 + Django REST Framework 3.16 |
| **Auth** | SimpleJWT (access + refresh tokens) |
| **Database** | PostgreSQL via psycopg2 |
| **Task Queue** | Celery with SQS broker (configurable) |
| **Storage** | S3 via django-storages + boto3 (with filesystem fallback) |
| **API Docs** | drf-spectacular (Swagger / ReDoc) |
| **DI Container** | dependency-injector |
| **Package Manager** | PDM |
| **Containerization** | Docker multi-stage + Supervisor + Nginx |
| **CI/CD** | GitHub Actions (lint + test + deploy) |
| **Deployment** | AWS Elastic Beanstalk (ECR + versioned bundles) |

---

## CLI Reference

### Create Mode

```bash
djinit <project_name> [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--python-version` | `3.12` | Python version for Dockerfile and pyproject.toml |
| `--django-version` | `5.2` | Django version constraint |
| `--drf-version` | `3.16` | DRF version constraint |
| `--author` | `CFAI` | Author name in pyproject.toml |
| `--description` | `""` | Project description |
| `--platform` | `aws-eb` | Deployment platform (determines which infra files are generated) |
| `--output-dir` | `.` | Parent directory for the new project |
| `--dry-run` | | Preview file list without writing anything |

```bash
# Preview what would be created
djinit myapi --dry-run

# Customize versions
djinit myapi --python-version 3.13 --django-version 5.3

# Specify platform explicitly
djinit myapi --platform aws-eb --description "Order service"
```

### Update Mode

Push template improvements to an existing project **without overwriting your
custom code** (`main/` and `base/` are never touched by updates).

```bash
# Update CI/CD workflows
djinit --update-ci --project-dir ./myproject

# Update Docker and infrastructure files
djinit --update-docker --update-infra --project-dir ./myproject

# Update everything updatable (CI + Docker + Infra + Root)
djinit --update-all --project-dir ./myproject

# Skip automatic backup
djinit --update-all --project-dir ./myproject --no-backup
```

Before overwriting, djinit shows a diff summary and creates a timestamped
backup in `.djinit-backup/`:

```
Updating 4 file(s) in /home/you/myproject:

  [CHANGED] (+12/-3 lines)        .github/workflows/ci.yml
  [UNCHANGED]                      .github/workflows/dev-cd.yml
  [UNCHANGED]                      .github/workflows/prod-cd.yml
  [NEW]                            .github/copilot-instructions.md

Backed up 1 file(s) to .djinit-backup/20250211_143022
Updated 2 file(s).
```

### Update Groups

| Group | Flag | Files Included |
|-------|------|----------------|
| **CI** | `--update-ci` | `.github/workflows/*`, `.github/copilot-instructions.md` |
| **Docker** | `--update-docker` | `Dockerfile`, `entrypoint.sh`, `release.sh`, `supervisord_*.conf` |
| **Infra** | `--update-infra` | `.platform/**`, `infra/*`, `nginx/*` |
| **Root** | _(via `--update-all`)_ | `.env`, `.gitignore`, `README.md`, `pyproject.toml`, `manage.py`, `conftest.py` |

> `--update-all` = CI + Docker + Infra + Root. The `main/` and `base/` apps
> are **never** updated — they belong to you.

### Info Commands

```bash
djinit --version          # Show djinit version
djinit --list-files       # Show template-to-output file mapping
```

---

## Platform Support

djinit uses a `--platform` flag to determine which deployment infrastructure
to generate. Templates are split into **common** (Django scaffolding, shared
across all platforms) and **platform-specific** (Docker, CD workflows, hooks).

| Platform | Flag Value | Status |
|----------|-----------|--------|
| AWS Elastic Beanstalk | `aws-eb` | Available (default) |
| Azure App Service | `azure` | Planned |
| Bare Docker / Compose | `docker` | Planned |

The platform is stored in `.djinit.json`, so `--update-*` commands
automatically use the correct platform for existing projects. Projects
created before the `--platform` flag was added default to `aws-eb`.

---

## How It Works

### Template Architecture

```
templates/
├── common/              # 30 files — platform-agnostic Django scaffolding
│   ├── main/            #   settings.py, celery.py, urls.py, wsgi.py, ...
│   ├── base/            #   models, views, DI container, pagination, ...
│   ├── github/           #   CI workflow, copilot instructions
│   └── (root files)     #   .env, pyproject.toml, manage.py, ...
└── platforms/
    └── aws_eb/          # 13 files — EB-specific deployment infra
        ├── github/workflows/   dev-cd.yml, prod-cd.yml
        ├── platform/hooks/     EB lifecycle hooks
        ├── nginx/              reverse proxy configs
        └── (root files)        Dockerfile, entrypoint, supervisord, ...
```

Three "mixed" templates (`settings.py.j2`, `pyproject.toml.j2`, `dotenv.j2`)
live in `common/` and use `{% if platform == "aws-eb" %}` conditionals for
their small cloud-specific sections (S3 storage, SQS broker, RDS detection).

### Rendering Pipeline

1. **Manifest** merges common + platform files into a single file map
2. **Renderer** processes `.j2` files through Jinja2, copies static files verbatim
3. **Generator** writes rendered files to disk, sets `+x` on `.sh` files, writes `.djinit.json`
4. **Updater** reads `.djinit.json`, re-renders selected groups, shows diffs, creates backups

---

## Configuration File

Every generated project contains a `.djinit.json` at the root:

```json
{
  "djinit_version": "0.1.0",
  "platform": "aws-eb",
  "project_name": "myproject",
  "python_version": "3.12",
  "django_version": "5.2",
  "drf_version": "3.16",
  "author": "Nao Intelligence",
  "description": "Payments API"
}
```

This file is used by `--update-*` commands to re-render templates with the
original context. **Do not delete it** if you want update support.

---

## Development

```bash
# Clone and install in editable mode with test dependencies
git clone https://github.com/Nao-Intelligence/djinit.git
cd djinit
pipx install -e ".[dev]"

# Run tests
pytest

# Run tests with verbose output
pytest -v
```

### Project Structure

```
djinit/
├── src/djinit/
│   ├── cli.py          # Argument parsing and entry point
│   ├── manifest.py     # Platform enum, file manifests, update groups
│   ├── renderer.py     # Jinja2 template rendering
│   ├── generator.py    # New project creation
│   ├── updater.py      # Selective file updates
│   ├── backup.py       # Timestamped backup before updates
│   ├── diff.py         # Change summary display
│   └── templates/      # Jinja2 templates (common/ + platforms/)
└── tests/
    ├── test_cli.py
    ├── test_generator.py
    ├── test_renderer.py
    └── test_updater.py
```

### Adding a New Platform

1. Create `templates/platforms/<platform_name>/` with deployment-specific files
2. Add a member to the `Platform` enum in `manifest.py`
3. Add the platform's file manifest to `PLATFORM_MANIFESTS`
4. Add `{% if platform == "<value>" %}` blocks to mixed templates if needed
5. Add tests and update this README

---

## GitHub Secrets Required (AWS EB)

For the generated CI/CD pipelines to work, configure these GitHub repository
secrets:

| Secret | Description |
|--------|-------------|
| `AWS_ACCOUNT_ID` | Your 12-digit AWS account ID |
| `AWS_REGION` | Deployment region (e.g. `eu-central-1`) |
| `GH_TOKEN` | GitHub token for Docker build args |

The CD workflows use **OIDC federation** (`role-to-assume`) — no static AWS
keys needed. Create an IAM role named `GHA-EB-Deploy` with EB, ECR, and S3
permissions, and configure its trust policy for GitHub Actions.
