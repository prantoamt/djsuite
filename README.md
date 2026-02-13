<div align="center">

# djinit

**Production-ready Django project scaffolding in one command.**

Generates a fully-configured Django + DRF project with Docker, CI/CD,
Celery, PostgreSQL, and cloud deployment — so you ship features on day one,
not boilerplate.

[![PyPI](https://img.shields.io/pypi/v/djinit?color=blue)](https://pypi.org/project/djinit/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![Django 5.x](https://img.shields.io/badge/django-5.x-092E20?logo=django&logoColor=white)](https://djangoproject.com)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

</div>

---

## Why djinit?

Every production Django project needs the same foundation: DRF, JWT auth,
Celery workers, PostgreSQL, Docker, CI/CD pipelines, and deployment config.
Setting this up by hand takes hours and inevitably drifts between projects.

**djinit solves this.** One command generates ~50 files with a proven
structure — and when the template evolves, `--update-*` flags push changes
to existing projects without touching your custom code.

---

## Install

```bash
pip install djinit
```

Or with [pipx](https://pipx.pypa.io/) (recommended for CLI tools):

```bash
pipx install djinit
```

## Quick Start

```bash
# Create a new project
djinit myproject --description "Payments API"

# Preview what would be created
djinit myproject --dry-run

# List all generated files
djinit --list-files
```

```
  created .env
  created .github/workflows/ci.yml
  created .github/workflows/dev-cd.yml
  created Dockerfile
  created main/settings.py
  created base/models.py
  ... (~50 files total)

Running pdm lock to pin dependencies...
  pdm.lock created

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

### Stack

| Layer | Technology |
|-------|-----------|
| **Framework** | Django 5.2 + Django REST Framework 3.16 |
| **Auth** | SimpleJWT (access + refresh tokens) |
| **Database** | PostgreSQL via psycopg2 |
| **Task Queue** | Celery (SQS broker on AWS, configurable) |
| **Storage** | S3 via django-storages (with filesystem fallback in dev) |
| **API Docs** | drf-spectacular (Swagger / ReDoc, DEBUG only) |
| **DI Container** | dependency-injector |
| **Package Manager** | PDM |
| **Containerization** | Docker multi-stage + Supervisor + Nginx |
| **CI/CD** | GitHub Actions (lint + test + deploy) |
| **Deployment** | AWS Elastic Beanstalk (default, extensible) |

### Generated Project Structure

```
myproject/
├── .djinit.json                      # djinit metadata (for update mode)
├── .env                              # Environment variables
├── .pre-commit-config.yaml           # black + isort hooks
├── docker-compose.yml                # Postgres + Redis for local dev
├── pyproject.toml                    # PDM project with all dependencies
├── Dockerfile                        # Multi-stage build (non-root user)
├── README.md                         # Project docs with architecture guide
├── CONTRIBUTING.md                   # Contributor guide
├── CHANGELOG.md                      # Auto-updated on production deploy
├── .github/
│   ├── copilot-instructions.md       # AI assistant context
│   ├── release.yml                   # Release note categories
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/
│       ├── ci.yml                    # Lint + test on every PR
│       ├── auto-label.yml            # Label PRs from branch prefix
│       ├── dev-cd.yml                # Deploy to dev + draft release
│       └── prod-cd.yml              # Deploy to prod + publish release
├── main/                             # Django project config
│   ├── settings.py                   # Env-based config with security defaults
│   ├── celery.py                     # Celery app
│   ├── urls.py                       # API routes + Swagger UI
│   └── wsgi.py / asgi.py
├── base/                             # Shared foundation app
│   ├── containers.py                 # Dependency injection
│   ├── models.py                     # TimeStampMixin base model
│   ├── views.py                      # Health check + Celery task status
│   ├── services/                     # Service layer
│   └── tests/                        # Per-app tests
└── (deployment files)                # entrypoint, nginx, supervisor, EB hooks
```

### Architecture Highlights

- **Service layer pattern** — business logic in `services/`, not in views or serializers
- **Dependency injection** — services wired through `dependency-injector`, mock-friendly testing
- **Health check** — `/health/` endpoint checks DB connectivity (200/503)
- **Security defaults** — HSTS, secure cookies, SSL redirect auto-enabled in production
- **Trunk-based CD** — branch prefix drives labels, changelogs, and deployments automatically
- **Non-root Docker** — container runs as unprivileged user with Nginx security headers

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
| `--author` | system username | Author name in pyproject.toml |
| `--description` | `""` | Project description |
| `--platform` | `aws-eb` | Deployment platform |
| `--output-dir` | `.` | Parent directory for the new project |
| `--dry-run` | | Preview file list without writing anything |

### Update Mode

Push template improvements to an existing project **without overwriting your
custom code** (`main/` and `base/` are never touched by updates).

```bash
djinit --update-ci --project-dir ./myproject       # CI/CD workflows
djinit --update-docker --project-dir ./myproject    # Docker files
djinit --update-infra --project-dir ./myproject     # Infrastructure files
djinit --update-all --project-dir ./myproject       # Everything updatable
djinit --update-all --no-backup --project-dir ./myproject  # Skip backup
```

Before overwriting, djinit shows a diff summary and creates a timestamped
backup in `.djinit-backup/`:

```
Updating 4 file(s) in /home/you/myproject:

  [CHANGED] (+12/-3 lines)        .github/workflows/ci.yml
  [UNCHANGED]                      .github/workflows/dev-cd.yml
  [NEW]                            .github/copilot-instructions.md

Backed up 1 file(s) to .djinit-backup/20250211_143022
Updated 2 file(s).
```

| Group | Flag | Files |
|-------|------|-------|
| **CI** | `--update-ci` | `.github/workflows/*`, copilot instructions, release config |
| **Docker** | `--update-docker` | `Dockerfile`, `entrypoint.sh`, `release.sh`, supervisord configs |
| **Infra** | `--update-infra` | `.platform/**`, `infra/*`, `nginx/*` |
| **Root** | _(via `--update-all`)_ | `.env`, `.gitignore`, `README.md`, `pyproject.toml`, etc. |

> `--update-all` = CI + Docker + Infra + Root. The `main/` and `base/` apps
> are **never** updated — they belong to you.

---

## Platform Support

| Platform | `--platform` | Status |
|----------|-------------|--------|
| AWS Elastic Beanstalk | `aws-eb` | Available (default) |
| Azure App Service | `azure` | Planned |
| Bare Docker / Compose | `docker` | Planned |

The platform is stored in `.djinit.json`, so `--update-*` commands
automatically use the correct platform. See [Contributing](CONTRIBUTING.md)
for how to add a new platform.

---

## How It Works

```
templates/
├── common/              # Platform-agnostic Django scaffolding
│   ├── main/            #   settings.py, celery.py, urls.py, wsgi.py, ...
│   ├── base/            #   models, views, DI container, pagination, ...
│   ├── github/          #   CI workflow, copilot instructions, release config
│   └── (root files)     #   .env, pyproject.toml, manage.py, ...
└── platforms/
    └── aws_eb/          # EB-specific deployment infra
        ├── github/workflows/   dev-cd.yml, prod-cd.yml
        ├── platform/hooks/     EB lifecycle hooks
        ├── nginx/              reverse proxy configs
        └── (root files)        Dockerfile, entrypoint, supervisord, ...
```

1. **Manifest** merges common + platform files into a single file map
2. **Renderer** processes `.j2` files through Jinja2, copies static files verbatim
3. **Generator** writes rendered files, sets `+x` on scripts, writes `.djinit.json`, runs `pdm lock`
4. **Updater** reads `.djinit.json`, re-renders selected groups, shows diffs, creates backups

---

## CI/CD Setup

**CI** runs on every pull request with zero configuration — no GitHub Secrets needed.

**CD (AWS EB)** requires two repository secrets for deployment:

| Secret | Description |
|--------|-------------|
| `AWS_ACCOUNT_ID` | Your 12-digit AWS account ID |
| `DEV_AWS_REGION` | Dev deployment region (e.g. `eu-central-1`) |
| `PROD_AWS_REGION` | Prod deployment region (e.g. `eu-central-1`) |

The CD workflows authenticate via **OIDC federation** — no static AWS keys. Create an IAM role named `GHA-EB-Deploy` with Elastic Beanstalk, ECR, and S3 permissions, and configure its trust policy for GitHub Actions.

---

## Releasing

1. Trigger the **Release** workflow manually via GitHub Actions (`workflow_dispatch`)
2. The workflow computes the next semver from PR labels since the last tag:
   - `breaking` label → **major** bump
   - `feature` label → **minor** bump
   - `fix`, `chore`, `docs` → **patch** bump
3. Tests run, package is built and published to PyPI
4. A GitHub release is created with categorized notes
5. `pyproject.toml`, `__init__.py`, and `CHANGELOG.md` are updated automatically

Requires [PyPI trusted publishing](https://docs.pypi.org/trusted-publishers/) configured for this repository.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, project
structure, and how to add templates or platforms.

## License

[MIT](LICENSE)
