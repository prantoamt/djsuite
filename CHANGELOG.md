# Changelog

## v0.0.3 (2026-02-13)

<!-- Release notes generated using configuration in .github/release.yml at main -->

## What's Changed
### Maintenance
* Chore update pipeline by @prantoamt in https://github.com/prantoamt/djsuite/pull/6


**Full Changelog**: https://github.com/prantoamt/djsuite/compare/v0.0.2...v0.0.3

## v0.0.2 (2026-02-13)

<!-- Release notes generated using configuration in .github/release.yml at main -->

## What's Changed
### Maintenance
* chore: split release workflow, add linting and copilot instructions by @prantoamt in https://github.com/prantoamt/djsuite/pull/2


**Full Changelog**: https://github.com/prantoamt/djsuite/compare/v0.0.1...v0.0.2

## 0.1.0 (2025-01-01)

Initial release.

- Django + DRF project scaffolding with a single command
- AWS Elastic Beanstalk deployment templates (Dockerfile, CD workflows, EB hooks)
- Common templates: settings, Celery, JWT auth, DI container, health check
- GitHub Actions CI/CD (lint + test + deploy)
- Selective update mode (`--update-ci`, `--update-docker`, `--update-infra`, `--update-all`)
- Automatic backup before updates with diff summary
- Dry-run and list-files preview commands
- Platform-extensible manifest architecture
