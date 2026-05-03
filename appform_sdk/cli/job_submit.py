"""Job submit dynamic parser builder and handler helpers."""

import argparse
import json
import sys

from appform_sdk.cli.common import SubmitHelpFormatter
from appform_sdk.job_profiles import JobProfileManager
from appform_sdk.job_submit import _apply_path_conversion, _resolve_disk_mapping

# ---------------------------------------------------------------------------
# Profile loading
# ---------------------------------------------------------------------------


def resolve_profile_config(args):
    profile_config = getattr(args, "profile_config", None)
    if not profile_config:
        from appform_sdk.config import Config

        cfg = Config(config_file=getattr(args, "config_file", None))
        profile_config = cfg.job_profile_config
    return profile_config


def load_pm(args):
    return JobProfileManager(config_file=resolve_profile_config(args))


# ---------------------------------------------------------------------------
# Submit parser building
# ---------------------------------------------------------------------------


def build_submit_parser(pm, app_id, profile, supported):
    """Build a full argparse parser with app-specific parameters."""
    p = argparse.ArgumentParser(
        prog=f"appform jobs submit -a {app_id}",
        description=f"Universal job submission tool for Appform SDK.",
        formatter_class=SubmitHelpFormatter,
        epilog=_build_epilog(pm, app_id, profile, supported),
    )

    p.add_argument(
        "-a",
        "--app",
        choices=supported,
        default=app_id,
        metavar="{" + ",".join(supported) + "}",
        help="Select application type",
    )
    p.add_argument(
        "-l",
        "--list-apps",
        action="store_true",
        dest="list_apps",
        help="List all supported applications",
    )
    p.add_argument(
        "--set",
        action="append",
        dest="set_params",
        metavar="KEY=VALUE",
        help="Override any JH_* parameter (repeatable)",
    )
    p.add_argument(
        "--params", dest="json_params", help="Override parameters as JSON string"
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="Only show final parameters, do not submit",
    )

    required_params = [x for x in profile.parameters if x.required]
    optional_params = [x for x in profile.parameters if not x.required]

    if required_params:
        group = p.add_argument_group(f"{profile.name} required parameters")
        _add_params_to_group(group, required_params)
    if optional_params:
        group = p.add_argument_group(f"{profile.name} optional parameters")
        _add_params_to_group(group, optional_params)

    return p


def _add_params_to_group(group, params):
    """Add ParameterDef objects as argparse arguments."""
    for pd in params:
        arg_options = []
        if pd.short_arg:
            arg_options.append(f"-{pd.short_arg}")
        arg_options.append(f"--{pd.effective_cli_name}")

        help_text = pd.description
        if pd.default:
            help_text += f" (default: {pd.default})"
        if pd.required:
            help_text += " [REQUIRED]"

        metavar = None
        if pd.param_type == "upload":
            metavar = "FILE"
        elif pd.default:
            metavar = str(pd.default).upper()
        else:
            metavar = pd.effective_cli_name.replace("-", "_").upper()

        kwargs = {
            "dest": f"param_{pd.effective_cli_name.replace('-', '_')}",
            "help": help_text,
        }

        if pd.param_type == "switch":
            kwargs["nargs"] = "?"
            kwargs["const"] = "on"
            kwargs["choices"] = ["on", "off"]
            kwargs["metavar"] = "{on,off}"
            kwargs["default"] = pd.default if pd.default else "off"
        else:
            kwargs["metavar"] = metavar

        group.add_argument(*arg_options, **kwargs)


def _build_epilog(pm, app_id, profile, supported):
    """Build help epilog text."""
    lines = []
    lines.append(f"Supported applications: {', '.join(supported)}")
    lines.append("")
    lines.append("Usage examples:")
    lines.append(f"  appform jobs submit -a {app_id} -i /path/to/file.sim --ncpu 8")
    lines.append(
        f"  appform jobs submit -a {app_id} --set JH_CAS=/path/to/file --set JH_NCPU=8"
    )
    lines.append(f"  appform jobs submit -a {app_id} --dry-run -i /path/to/file.sim")
    lines.append(
        f"  appform jobs submit -l                                     # list apps"
    )
    lines.append(
        f"  appform jobs submit -a {app_id} --help                     # this help"
    )
    lines.append("")

    required = profile.get_required_params()
    if required:
        lines.append(f"{profile.name} required parameters:")
        for pd in required:
            if pd.cli_arg and pd.short_arg:
                arg_str = f"  -{pd.short_arg}, --{pd.cli_arg}"
            elif pd.cli_arg:
                arg_str = f"  --{pd.cli_arg}"
            elif pd.short_arg:
                arg_str = f"  -{pd.short_arg}, --{pd.effective_cli_name}"
            else:
                arg_str = f"  --{pd.effective_cli_name}"
            lines.append(f"{arg_str:<30} {pd.description}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Submit handler
# ---------------------------------------------------------------------------


def handle_jobs_submit(pm, raw_args, output_format):
    """
    Full handler for ``appform jobs submit``.

    Two-pass parsing:
      Pass 1 (quick): extract -a/-l from raw_args
      Pass 2 (full):  build per-app parser, parse everything including --help
    """
    supported = [a["app_id"] for a in pm.list_apps()]
    disk_mapping = _resolve_disk_mapping(pm)

    # --- Pass 1: quick pre-parse ---
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("-a", "--app", dest="_app", default=None)
    pre.add_argument("-l", "--list-apps", dest="_list_apps", action="store_true")
    pre_args, _ = pre.parse_known_args(raw_args)

    # -l: list apps
    if pre_args._list_apps:
        apps = pm.list_apps()
        if output_format == "json":
            print(
                json.dumps(
                    {"applications": apps, "config_file": pm.config_file},
                    indent=2,
                    ensure_ascii=False,
                )
            )
        else:
            print_apps_table(apps)
            if pm.config_file:
                print(f"\nConfig: {pm.config_file}")
            if disk_mapping:
                print("\nWindows path mapping:")
                for drive, path in disk_mapping.items():
                    print(f"  {drive} -> {path}")
        return

    app_id = pre_args._app

    if not app_id:
        # No -a given: show generic submit help
        print(f"Supported applications: {', '.join(supported)}")
        print(f"\nUsage:")
        print(
            f"  appform jobs submit -a <app> [options]   # Submit with app-specific args"
        )
        print(f"  appform jobs submit -l                   # List all applications")
        print(f"  appform jobs submit -a <app> --help      # Show app-specific help")
        if disk_mapping:
            print("\nWindows path mapping:")
            for drive, path in disk_mapping.items():
                print(f"  {drive} -> {path}")
        return

    # --- Resolve profile ---
    profile = pm.get_profile(app_id)
    if not profile:
        print(
            f"Error: Unknown application '{app_id}'. Available: {', '.join(supported)}",
            file=sys.stderr,
        )
        sys.exit(1)

    # --- Pass 2: build full parser and parse ---
    full_parser = build_submit_parser(pm, app_id, profile, supported)
    try:
        parsed = full_parser.parse_args(raw_args)
    except SystemExit as e:
        if e.code == 0:
            return  # --help triggered exit
        raise  # re-raise argparse errors so user sees them

    if parsed.list_apps:
        apps = pm.list_apps()
        if output_format == "json":
            print(
                json.dumps(
                    {"applications": apps, "config_file": pm.config_file},
                    indent=2,
                    ensure_ascii=False,
                )
            )
        else:
            print_apps_table(apps)
            if disk_mapping:
                print("\nWindows path mapping:")
                for drive, path in disk_mapping.items():
                    print(f"  {drive} -> {path}")
        return

    # --- Collect overrides ---
    overrides = {}
    for pd in profile.parameters:
        attr = f"param_{pd.effective_cli_name.replace('-', '_')}"
        val = getattr(parsed, attr, None)
        if val is not None:
            if pd.param_type == "switch":
                overrides[pd.name] = str(val)
            elif val not in (None, ""):
                overrides[pd.name] = str(val)

    if parsed.set_params:
        for item in parsed.set_params:
            if "=" not in item:
                print(
                    f"Error: Invalid format '{item}'. Expected KEY=VALUE.",
                    file=sys.stderr,
                )
                sys.exit(1)
            k, v = item.split("=", 1)
            overrides[k] = v

    if parsed.json_params:
        try:
            overrides.update(json.loads(parsed.json_params))
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in --json-params: {e}", file=sys.stderr)
            sys.exit(1)

    # --- Windows path conversion ---
    overrides = _apply_path_conversion(overrides, disk_mapping)

    # --- Build params ---
    try:
        params = pm.build_submit_params(app_id, overrides)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # --- Dry run ---
    if parsed.dry_run:
        print(f"Application: {app_id} ({profile.name})")
        print(f"Parameters:")
        print(json.dumps(params, indent=2, ensure_ascii=False))
        return

    # --- Submit ---
    return app_id, params


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def print_apps_table(apps):
    print(f"{'App ID':<25} {'Name':<25} Description")
    print("-" * 80)
    for app in apps:
        print(f"{app['app_id']:<25} {app['name']:<25} {app['description']}")


def print_app_params(profile):
    print(f"Application: {profile.app_id} - {profile.name}")
    if profile.description:
        print(f"Description: {profile.description}")
    print()
    print(
        f"{'Parameter':<25} {'Type':<8} {'Required':<8} {'Default':<12} {'CLI Arg':<12} {'Short':<6} Description"
    )
    print("-" * 110)
    for p in profile.parameters:
        req = "Yes" if p.required else ""
        default = p.default or ""
        cli = p.cli_arg or p.effective_cli_name
        short = f"-{p.short_arg}" if p.short_arg else ""
        print(
            f"{p.name:<25} {p.param_type:<8} {req:<8} {default:<12} {cli:<12} {short:<6} {p.description}"
        )

    required = profile.get_required_params()
    if required:
        example_parts = []
        for p in required:
            if p.cli_arg:
                example_parts.append(f"--{p.cli_arg} VALUE")
            elif p.short_arg:
                example_parts.append(f"-{p.short_arg} VALUE")
            else:
                name = p.name.lower().replace("jh_", "").replace("_", "-")
                example_parts.append(f"--{name} VALUE")
        print(f"\nUsage example:")
        print(f"  appform jobs submit -a {profile.app_id} {' '.join(example_parts)}")
        print(
            f"  appform jobs submit -a {profile.app_id} --set JH_CAS=/path/to/file --set JH_NCPU=8"
        )
