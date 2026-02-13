# Copilot Instructions for djsuite

## What is djsuite

A CLI tool that scaffolds production-ready Django + DRF projects in one command. It generates ~50 files with Docker, CI/CD, Celery, PostgreSQL, and AWS Elastic Beanstalk configuration. Built with a manifest-based template engine that supports selective updates to existing projects. Published on PyPI as `djsuite`.

## Architecture

The codebase follows a pipeline: **CLI parsing -> manifest resolution -> template rendering -> file writing**.

### Core Modules (`src/djsuite/`)

- `cli.py` — Entry point. Two modes: Create (scaffold new project) and Update (push template changes via `--update-*` flags).
- `manifest.py` — Central registry of all generated files. `Platform` enum defines deployment targets. `UpdateGroup` enum defines selective update scopes. `get_manifest()` merges common + platform-specific file lists.
- `renderer.py` — Jinja2 environment with `StrictUndefined`. Handles both `.j2` templates and static files.
- `generator.py` — Writes rendered files to disk, sets executable bit on `.sh` files, writes `.djsuite.json` metadata.
- `updater.py` — Loads context from `.djsuite.json`, re-renders only selected file groups, creates backups, shows diff summary. Never touches user app code.
- `backup.py` — Timestamped backups in `.djsuite-backup/`.
- `diff.py` — Compares old vs new content, reports `[NEW]`, `[UNCHANGED]`, `[CHANGED]`.

### Template Organization

Templates live in `src/djsuite/templates/` split into:
- `common/` (~38 files) — Platform-agnostic: Django apps, settings, CI workflow, pyproject.toml, .env, docker-compose, pre-commit, etc.
- `platforms/aws_eb/` (13 files) — Dockerfile, entrypoint, CD workflows, EB hooks, nginx, supervisord.

Three "mixed" templates (`settings.py.j2`, `pyproject.toml.j2`, `dotenv.j2`) use `{% if platform == "aws-eb" %}` conditionals for platform-specific sections.

## Key Design Decisions

- **Manifest-driven**: Adding files requires only updating the manifest dict in `manifest.py` — no changes to core logic.
- **Adding new platforms**: Add enum value to `Platform`, create `PLATFORM_MANIFESTS` entry, add templates under `templates/platforms/<name>/`.
- **Stateful updates**: `.djsuite.json` stores original context so updates can re-render without user re-entering options.
- **GitHub Actions escaping**: Templates must preserve `${{ }}` syntax — Jinja2's `{% raw %}` blocks handle this.

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check src/ tests/
ruff format --check src/ tests/
```

Tests that call `generate()` are slow (~30s each) because `pdm lock` runs during project creation. Tests use `tmp_path` for filesystem isolation.
