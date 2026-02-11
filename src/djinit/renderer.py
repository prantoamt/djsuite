"""Jinja2 template rendering and path mapping."""

import importlib.resources

import jinja2


def _get_template_dir():
    """Get the path to the templates directory."""
    return importlib.resources.files("djinit") / "templates"


def create_environment():
    """Create a Jinja2 environment configured for our templates."""
    template_dir = _get_template_dir()
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_dir)),
        keep_trailing_newline=True,
        undefined=jinja2.StrictUndefined,
    )
    return env


def render_template(dir_prefix, template_path, context):
    """Render a single template with the given context.

    Args:
        dir_prefix: subdirectory prefix (e.g. "common" or "platforms/aws_eb")
        template_path: path relative to the dir_prefix
        context: template variables dict

    For .j2 templates, renders with Jinja2.
    For static files (no .j2 suffix), reads the file content verbatim.
    """
    full_template_path = f"{dir_prefix}/{template_path}"
    if template_path.endswith(".j2"):
        env = create_environment()
        template = env.get_template(full_template_path)
        return template.render(**context)
    else:
        template_dir = _get_template_dir()
        resource = template_dir / full_template_path
        return resource.read_text(encoding="utf-8")


def render_all(manifest, context):
    """Render all templates in the manifest.

    Args:
        manifest: dict of (dir_prefix, template_path) -> (output_path, group)
        context: template variables dict

    Returns:
        dict of output_path -> rendered_content
    """
    results = {}
    for (dir_prefix, template_path), (output_path, _group) in manifest.items():
        results[output_path] = render_template(dir_prefix, template_path, context)
    return results
