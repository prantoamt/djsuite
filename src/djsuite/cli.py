"""CLI entry point for djsuite."""

import argparse
import getpass

from djsuite import __version__
from djsuite.manifest import Platform, UpdateGroup, get_manifest


def _valid_project_name(value):
    """Validate and normalize project name to a valid Python identifier."""
    name = value.replace("-", "_")
    if not name.isidentifier():
        raise argparse.ArgumentTypeError(
            f"{value!r} is not a valid Python identifier (after replacing hyphens with underscores)"
        )
    return name


def build_parser():
    parser = argparse.ArgumentParser(
        prog="djsuite",
        description="Production-ready Django project scaffolding in one command.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    # Create mode
    parser.add_argument(
        "project_name",
        nargs="?",
        type=_valid_project_name,
        help="Name of the new Django project (must be a valid Python identifier)",
    )
    parser.add_argument("--python-version", default="3.12", help="Python version (default: 3.12)")
    parser.add_argument("--django-version", default="5.2", help="Django version (default: 5.2)")
    parser.add_argument("--drf-version", default="3.16", help="DRF version (default: 3.16)")
    parser.add_argument("--author", default=getpass.getuser(), help="Author name (default: system username)")
    parser.add_argument("--description", default="", help="Project description")
    parser.add_argument("--output-dir", default=".", help="Output directory (default: current dir)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created without writing files")
    parser.add_argument(
        "--platform",
        choices=[p.value for p in Platform],
        default="aws-eb",
        help="Deployment platform (default: aws-eb)",
    )

    # Update mode
    parser.add_argument("--update-ci", action="store_true", help="Update CI/CD files")
    parser.add_argument("--update-docker", action="store_true", help="Update Docker files")
    parser.add_argument("--update-infra", action="store_true", help="Update infrastructure files")
    parser.add_argument("--update-all", action="store_true", help="Update all updatable files")
    parser.add_argument("--project-dir", default=".", help="Project directory for updates (default: current dir)")
    parser.add_argument("--no-backup", action="store_true", help="Skip backup before updating")

    # Info
    parser.add_argument("--list-files", action="store_true", help="List all files that would be generated")

    return parser


def _get_update_groups(args):
    """Return the set of UpdateGroups to update based on CLI flags."""
    groups = set()
    if args.update_all:
        groups = {UpdateGroup.CI, UpdateGroup.DOCKER, UpdateGroup.INFRA, UpdateGroup.ROOT}
    else:
        if args.update_ci:
            groups.add(UpdateGroup.CI)
        if args.update_docker:
            groups.add(UpdateGroup.DOCKER)
        if args.update_infra:
            groups.add(UpdateGroup.INFRA)
    return groups


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    platform = Platform.from_str(args.platform)

    if args.list_files:
        manifest = get_manifest(platform)
        for (dir_prefix, template_path), (output_path, _group) in sorted(manifest.items(), key=lambda item: item[1][0]):
            print(f"  {dir_prefix + '/' + template_path:60s} -> {output_path}")
        return 0

    update_groups = _get_update_groups(args)

    if update_groups:
        from djsuite.updater import run_update

        return run_update(
            project_dir=args.project_dir,
            groups=update_groups,
            no_backup=args.no_backup,
        )

    if not args.project_name:
        parser.error("project_name is required for create mode (or use --update-* for update mode)")

    context = {
        "project_name": args.project_name,
        "python_version": args.python_version,
        "django_version": args.django_version,
        "drf_version": args.drf_version,
        "author": args.author,
        "description": args.description,
        "platform": platform.value,
    }

    if args.dry_run:
        from djsuite.generator import dry_run

        dry_run(context, args.output_dir, platform)
        return 0

    from djsuite.generator import generate

    generate(context, args.output_dir, platform)
    return 0
