# Contributing to djsuite

Thanks for your interest in contributing to djsuite!

## Setup

```bash
git clone https://github.com/prantoamt/djsuite.git
cd djsuite
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest           # run all tests
pytest -v        # verbose output
pytest -k test_name   # run a specific test
```

Note: tests that call `generate()` are slow (~30s each) because `pdm lock` runs during project creation.

## Project Structure

```
src/djsuite/
├── cli.py          # Argument parsing, entry point
├── manifest.py     # Platform enum, file manifests, update groups
├── renderer.py     # Jinja2 template rendering
├── generator.py    # New project creation
├── updater.py      # Selective file updates
├── backup.py       # Timestamped backups
├── diff.py         # Change summary display
└── templates/
    ├── common/           # Platform-agnostic templates (Django scaffold)
    └── platforms/
        └── aws_eb/       # AWS Elastic Beanstalk-specific templates
```

## How to Contribute

### Adding a Template File

1. Add the template to `src/djsuite/templates/common/` (or the appropriate platform directory).
2. Register it in `manifest.py` — add an entry to `COMMON_MANIFEST` or `PLATFORM_MANIFESTS` with the correct `UpdateGroup`.
3. If it's a Jinja2 template, name it with `.j2` extension. Static files are copied verbatim.
4. Add a test in `tests/test_generator.py` to verify the file is created and rendered correctly.

### Adding a New Platform

1. Add a member to the `Platform` enum in `manifest.py`.
2. Create `templates/platforms/<platform_name>/` with deployment-specific templates.
3. Add the platform's file manifest to `PLATFORM_MANIFESTS` in `manifest.py`.
4. Add `{% if platform == "<value>" %}` blocks to mixed templates (`settings.py.j2`, `pyproject.toml.j2`, `dotenv.j2`) if needed.
5. Add tests for the new platform.

### Branch Naming

Use conventional prefixes — PRs are auto-labeled and drive semver bumps:

| Prefix | Label | Version Bump |
|--------|-------|-------------|
| `feat-` | feature | minor |
| `fix-` | fix | patch |
| `breaking-` | breaking | major |
| `chore-` | chore | patch |
| `docs-` | documentation | patch |

### Pull Request Process

1. Fork the repo and create a branch from `main` (e.g. `feat-azure-platform`).
2. Make your changes.
3. Ensure all tests pass (`pytest`).
4. Open a PR with a clear description of what changed and why.

## Guidelines

- Keep templates minimal — generate what's needed, not everything possible.
- Maintain backwards compatibility with existing `.djsuite.json` files.
- Use `{% raw %}...{% endraw %}` in templates that contain GitHub Actions `${{ }}` expressions.
- Test template rendering — verify no unrendered `{{ }}` or `{% %}` in output.
