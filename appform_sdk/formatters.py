"""
Output formatters for Appform SDK CLI.

Transforms raw API responses into human-readable table/text formats.
Supports customizable output templates via YAML/JSON configuration.
"""

import json
import os
import re
from typing import Any, Callable, Dict, List, Optional

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


# Pre-compiled regex patterns for _format_text_template
_RE_MULTI_SPACE = re.compile(r" +")
_RE_PUNCT_UPPER = re.compile(r"([);,.])\s*([A-Z])")
_RE_LOWER_UPPER = re.compile(r"([a-z0-9])([A-Z]{2,})")
_RE_PAREN_UPPER = re.compile(r"(\))\s*([A-Z])")
_RE_SPACE_COMMA = re.compile(r" +,")
_RE_SPACE_SEMIC = re.compile(r" +;")
_RE_SPACE_DOT = re.compile(r" +\.")
_RE_DOUBLE_SPC = re.compile(r"  +")


# ---------------------------------------------------------------------------
# Default output templates
# ---------------------------------------------------------------------------

DEFAULT_TEMPLATES = {
    "jobs.list": {
        "type": "table",
        "title": "Jobs",
        "total_key": "data.total",
        "items_path": "data.jobs",
        "fields": [
            {"key": "jobId", "label": "JOB_ID", "width": 10},
            {"key": "status", "label": "STATUS", "width": 8},
            {"key": "name", "label": "NAME", "width": 30},
            {"key": "appName", "label": "APP", "width": 15},
            {"key": "queue", "label": "QUEUE", "width": 10},
            {"key": "owner", "label": "OWNER", "width": 12},
            {"key": "slots", "label": "SLOTS", "width": 6},
            {"key": "submitTime", "label": "SUBMIT_TIME", "width": 20},
        ],
    },
    "jobs.get": {
        "type": "detail",
        "title": "Job Detail",
        "item_path": "data",
        "fields": [
            {"key": "jobId", "label": "Job ID"},
            {"key": "name", "label": "Name"},
            {"key": "status", "label": "Status"},
            {"key": "appName", "label": "Application"},
            {"key": "queue", "label": "Queue"},
            {"key": "owner", "label": "Owner"},
            {"key": "userNameCn", "label": "Owner(CN)"},
            {"key": "slots", "label": "Slots"},
            {"key": "executionHost", "label": "Host", "format": "join"},
            {"key": "host", "label": "Host"},
            {"key": "submitTime", "label": "Submit Time"},
            {"key": "executionTime", "label": "Start Time"},
            {"key": "terminationTime", "label": "End Time"},
            {"key": "cwd", "label": "Working Dir"},
            {"key": "project", "label": "Project"},
            {"key": "gpuNum", "label": "GPU"},
            {"key": "reasons", "label": "Reasons", "format": "join"},
            {"key": "alarmInfo", "label": "Alarm"},
            {"key": "exceptionInfo", "label": "Exception"},
            {"key": "organizationTree", "label": "Organization"},
        ],
    },
    "sessions.list": {
        "type": "table",
        "title": "Sessions",
        "total_key": "data.total",
        "items_path": "data.sessions",
        "fields": [
            {"key": "session_id", "label": "SESSION_ID", "width": 12},
            {"key": "id", "label": "SESSION_ID", "width": 12},
            {"key": "app_id", "label": "APP", "width": 20},
            {"key": "owner", "label": "OWNER", "width": 15},
            {"key": "host", "label": "HOST", "width": 20},
            {"key": "status", "label": "STATUS", "width": 10},
            {"key": "createDate", "label": "CREATE_TIME", "width": 20},
        ],
    },
    "files.list": {
        "type": "table",
        "title": "Files",
        "items_path": "data",
        "fields": [
            {
                "key": "fileName",
                "label": "NAME",
                "width": 30,
                "prefix_key": "fileType",
                "prefix_map": {"directory": "[D]", "file": "[F]"},
            },
            {"key": "owner", "label": "OWNER", "width": 12},
            {"key": "size", "label": "SIZE", "width": 10, "format": "size"},
            {"key": "ts", "label": "MODIFIED", "width": 20},
        ],
    },
    "apps.list": {
        "type": "table",
        "title": "Applications",
        "items_path": "data",
        "fields": [
            {"key": "id", "label": "APP_ID", "width": 25},
            {"key": "name", "label": "NAME", "width": 25},
            {"key": "type", "label": "TYPE", "width": 8, "fallback": "mode"},
            {"key": "protocol", "label": "PROTOCOL", "width": 10},
            {"key": "os", "label": "OS", "width": 8},
        ],
    },
    "users.list": {
        "type": "table",
        "title": "Users",
        "total_key": "data.totalCount",
        "items_path": "data.list",
        "fields": [
            {"key": "userName", "label": "USERNAME", "width": 15},
            {"key": "userNameCn", "label": "DISPLAY_NAME", "width": 15},
            {
                "key": "userDepNameCn",
                "label": "DEPARTMENT",
                "width": 12,
                "fallback": "userDepName",
            },
            {"key": "userStat", "label": "STATUS", "width": 8},
            {"key": "userMail", "label": "EMAIL", "width": 25},
        ],
    },
    "departments.list": {
        "type": "tree",
        "title": "Departments",
        "items_path": "data",
        "name_key": "displayName",
        "fallback_name_key": "name",
        "children_key": "items",
    },
}


# ---------------------------------------------------------------------------
# Template management
# ---------------------------------------------------------------------------

_custom_templates: Dict[str, dict] = {}
_template_file: Optional[str] = None
_builtin_template_loaded = False


def _get_builtin_template_path() -> str:
    """Get path to the built-in output_templates.yaml bundled with the SDK."""
    return os.path.join(os.path.dirname(__file__), "output_templates.yaml")


def _ensure_builtin_loaded() -> None:
    """Load built-in templates on first use."""
    global _builtin_template_loaded
    if _builtin_template_loaded:
        return
    _builtin_template_loaded = True
    builtin = _get_builtin_template_path()
    if os.path.exists(builtin):
        _load_file(builtin)


def _load_file(file_path: str) -> None:
    """Load templates from a YAML or JSON file."""
    global _custom_templates, _template_file

    path = os.path.expanduser(file_path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Template file not found: {file_path}")

    if path.endswith((".yaml", ".yml")):
        if not YAML_AVAILABLE:
            raise ImportError(
                "PyYAML required for YAML templates. Install: pip install PyYAML"
            )
        with open(path, "r", encoding="utf-8") as f:
            templates = yaml.safe_load(f)
    elif path.endswith(".json"):
        with open(path, "r", encoding="utf-8") as f:
            templates = json.load(f)
    else:
        raise ValueError(
            f"Unsupported template format: {path}. Use .yaml, .yml, or .json"
        )

    if isinstance(templates, dict):
        # Strip meta keys (version, description, etc.) — only keep command entries
        for key, value in templates.items():
            if isinstance(value, dict) and ("fields" in value or "type" in value):
                _custom_templates[key] = value
        _template_file = path


def load_templates(file_path: str) -> None:
    """
    Load custom output templates from a YAML or JSON file.

    Custom templates override built-in defaults for matching command names.

    Args:
        file_path: Path to template file (.yaml/.yml or .json)

    Template format (YAML):
        ```yaml
        jobs.list:
          type: table
          title: My Custom Jobs View
          items_path: data.jobs
          total_key: data.total
          fields:
            - key: jobId
              label: ID
              width: 8
            - key: name
              label: Job Name
              width: 30
            - key: status
              label: ST
              width: 5
            - key: owner
              label: User
              width: 10
            - key: submitTime
              label: Submitted
              width: 19

        jobs.get:
          type: detail
          title: Job Info
          item_path: data
          fields:
            - key: jobId
              label: ID
            - key: name
              label: Name
            - key: status
              label: Status
        ```
    """
    _load_file(file_path)


def get_template(command: str, api_version: str = None) -> Optional[dict]:
    """Get template for a command, custom overrides default. Filters by version."""
    _ensure_builtin_loaded()

    # Custom templates first
    if command in _custom_templates:
        t = _custom_templates[command]
    else:
        t = DEFAULT_TEMPLATES.get(command)

    if t is None:
        return None

    # Check version compatibility
    if api_version and "min_version" in t:
        if _compare_versions(api_version, t["min_version"]) < 0:
            return None

    # Deep copy and filter fields by version
    import copy

    t = copy.deepcopy(t)
    if api_version and "fields" in t:
        t["fields"] = [
            f
            for f in t["fields"]
            if "min_version" not in f
            or _compare_versions(api_version, f["min_version"]) >= 0
        ]

    return t


def _compare_versions(v1: str, v2: str) -> int:
    """Compare version strings. Returns -1, 0, 1."""
    parts1 = [int(x) for x in v1.split(".")]
    parts2 = [int(x) for x in v2.split(".")]
    for p1, p2 in zip(parts1, parts2):
        if p1 < p2:
            return -1
        if p1 > p2:
            return 1
    if len(parts1) < len(parts2):
        return -1
    if len(parts1) > len(parts2):
        return 1
    return 0


def list_templates() -> Dict[str, str]:
    """List all available templates with their source."""
    _ensure_builtin_loaded()
    result = {}
    for cmd in DEFAULT_TEMPLATES:
        if cmd in _custom_templates:
            result[cmd] = f"custom ({_template_file})"
        else:
            result[cmd] = "built-in"
    for cmd in _custom_templates:
        if cmd not in DEFAULT_TEMPLATES:
            result[cmd] = f"custom ({_template_file})"
    return result


def resolve_template_file(cli_arg: str = None, config=None) -> Optional[str]:
    """
    Resolve template file path with priority:
    1. CLI --output-template
    2. APPFORM_OUTPUT_TEMPLATE env var
    3. config.json output_template field
    4. Built-in output_templates.yaml (auto-loaded)
    """
    if cli_arg:
        return cli_arg

    env_val = os.environ.get("APPFORM_OUTPUT_TEMPLATE")
    if env_val:
        return env_val

    if config and hasattr(config, "output_template") and config.output_template:
        return config.output_template

    return None


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


def _truncate(s: str, width: int) -> str:
    """Truncate string to width, adding '..' if needed."""
    s = str(s) if s is not None else ""
    if len(s) <= width:
        return s
    return s[: width - 2] + ".."


def _format_size(size) -> str:
    """Format byte size to human readable."""
    try:
        size = int(size)
    except (TypeError, ValueError):
        return str(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(size) < 1024:
            return f"{size:.0f}{unit}" if unit == "B" else f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}PB"


def _resolve_path(obj: dict, path: str):
    """Resolve dotted path like 'data.0.name' from nested dict/list."""
    parts = path.split(".")
    current = obj
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return current


def _get_field_value(item: dict, field_def: dict) -> str:
    """Extract a field value from an item using field definition."""
    key = field_def["key"]
    value = item.get(key)

    # Fallback key
    if value is None and "fallback" in field_def:
        value = item.get(field_def["fallback"])

    # Prefix
    prefix = ""
    if "prefix_key" in field_def:
        prefix_val = item.get(field_def["prefix_key"], "")
        prefix_map = field_def.get("prefix_map", {})
        prefix = prefix_map.get(str(prefix_val), "")

    # Format
    fmt = field_def.get("format")
    if fmt == "size":
        value = _format_size(value)
    elif fmt == "join" and isinstance(value, list):
        value = ", ".join(str(v) for v in value)
    elif fmt == "json" and isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False)

    value = str(value) if value is not None else ""

    if prefix:
        value = f"{prefix} {value}"

    return value


# ---------------------------------------------------------------------------
# Table formatter
# ---------------------------------------------------------------------------


def _table(
    headers: List[str], rows: List[List[str]], widths: Optional[List[int]] = None
) -> str:
    """Format data as an ASCII table."""
    if not rows:
        return "(empty)"

    col_count = len(headers)
    if widths is None:
        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row[:col_count]):
                widths[i] = max(widths[i], len(str(cell)))
        widths = [min(w, 50) for w in widths]

    header_line = "  ".join(
        _truncate(h, widths[i]).ljust(widths[i]) for i, h in enumerate(headers)
    )
    sep_line = "  ".join("-" * widths[i] for i in range(col_count))

    lines = [header_line, sep_line]
    for row in rows:
        cells = []
        for i in range(col_count):
            val = str(row[i]) if i < len(row) and row[i] is not None else ""
            cells.append(_truncate(val, widths[i]).ljust(widths[i]))
        lines.append("  ".join(cells))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Response data extractors
# ---------------------------------------------------------------------------


def _extract_list_data(response: dict, list_key: str = None) -> tuple:
    """Extract (total, items) from API response."""
    data = response.get("data")
    if data is None:
        return 0, []
    if isinstance(data, list):
        return len(data), data
    if isinstance(data, dict):
        if list_key and list_key in data:
            items = data[list_key]
            total = data.get("total", data.get("totalCount", len(items)))
            return total, items if isinstance(items, list) else []
        for key in ("jobs", "list", "sessions", "apps", "items", "records"):
            if key in data and isinstance(data[key], list):
                total = data.get("total", data.get("totalCount", len(data[key])))
                return total, data[key]
        return 1, [data]
    return 0, []


# ---------------------------------------------------------------------------
# Template-driven formatters
# ---------------------------------------------------------------------------


def _format_table_template(template: dict, response: dict) -> str:
    """Format using a table template."""
    # Extract total
    total = None
    if "total_key" in template:
        total = _resolve_path(response, template["total_key"])

    # Extract items
    items = _resolve_path(response, template.get("items_path", "data"))
    if items is None:
        items = []
    if isinstance(items, dict):
        items = [items]
    if not isinstance(items, list):
        items = []

    # Deduplicate field keys (for fallback: session_id vs id)
    fields = template.get("fields", [])
    headers = []
    widths = []
    seen_labels = set()
    for f in fields:
        label = f.get("label", f["key"])
        if label not in seen_labels:
            headers.append(label)
            widths.append(f.get("width", 20))
            seen_labels.add(label)

    rows = []
    for item in items:
        row = []
        seen_labels_row = set()
        for f in fields:
            label = f.get("label", f["key"])
            if label in seen_labels_row:
                continue
            seen_labels_row.add(label)
            row.append(_get_field_value(item, f))
        rows.append(row)

    lines = []
    if total is not None:
        lines.append(f"Total: {total}")
        lines.append("")
    lines.append(_table(headers, rows, widths))
    return "\n".join(lines)


def _format_detail_template(template: dict, response: dict) -> str:
    """Format using a detail (key-value) template."""
    item = _resolve_path(response, template.get("item_path", "data"))
    if item is None:
        return None  # Fall through to built-in
    if isinstance(item, list):
        item = item[0] if item else {}
    if not isinstance(item, dict):
        return str(item)

    fields = template.get("fields", [])
    if not fields:
        return None  # No fields defined, fall through to built-in

    pairs = []
    for f in fields:
        value = _get_field_value(item, f)
        if value and value != "0" and value != "[]":
            label = f.get("label", f["key"])
            pairs.append((label, value))

    if not pairs:
        return None  # All fields empty, fall through

    max_label = max(len(p[0]) for p in pairs)
    lines = []
    if template.get("title"):
        lines.append(template["title"])
        lines.append("")
    for label, value in pairs:
        lines.append(f"  {label:<{max_label}} : {value}")
    return "\n".join(lines)


def _format_tree_template(template: dict, response: dict) -> str:
    """Format using a tree template."""
    items = _resolve_path(response, template.get("items_path", "data"))
    if not items:
        return "(no data)"
    if not isinstance(items, list):
        items = [items]

    name_key = template.get("name_key", "name")
    fallback_name_key = template.get("fallback_name_key")
    children_key = template.get("children_key", "items")

    lines = []

    def walk(nodes, indent=0):
        for node in nodes:
            name = node.get(name_key)
            if not name and fallback_name_key:
                name = node.get(fallback_name_key, "")
            lines.append(f"{'  ' * indent}{name}")
            children = node.get(children_key, [])
            if children:
                walk(children, indent + 1)

    walk(items)
    return "\n".join(lines)


def _format_text_template(template: dict, response: dict) -> str:
    """Format using a text template — outputs raw field values."""
    items = _resolve_path(response, template.get("items_path", "data"))
    if not items:
        return "(no data)"
    if not isinstance(items, list):
        items = [items]

    fields = template.get("fields", [])
    if not fields:
        return json.dumps(items, indent=2, ensure_ascii=False)

    key = fields[0].get("key", "")
    result_lines = []
    for item in items:
        val = item.get(key, "")
        if val is None:
            val = ""
        # Server output has wide-space column padding (>=16 spaces).
        # Wide gap: if it splits a lowercase word → remove.
        # Otherwise → single space. 4-15 spaces → single space. <4 → keep.

        def _replace_space(m):
            length = len(m.group(0))
            if length < 4:
                return m.group(0)
            if length <= 15:
                return " "
            before_char = val[m.start() - 1] if m.start() > 0 else " "
            rest = val[m.end() :]
            after_char = ""
            for ch in rest:
                if ch != " ":
                    after_char = ch
                    break
            if (before_char.islower() and after_char.islower()) or (
                before_char in "-." and after_char.islower()
            ):
                return ""
            return " "

        cleaned = _RE_MULTI_SPACE.sub(_replace_space, val)
        # Fix glued punctuation → uppercase: ")Fri" → ") Fri", ";Fri" → "; Fri"
        cleaned = _RE_PUNCT_UPPER.sub(r"\1 \2", cleaned)
        # Fix glued lowercase → uppercase run: "minFri" → "min Fri"
        cleaned = _RE_LOWER_UPPER.sub(r"\1 \2", cleaned)
        # Fix glued closing paren → uppercase: ")Fri" → ") Fri"
        cleaned = _RE_PAREN_UPPER.sub(r"\1 \2", cleaned)
        # Fix space before comma/semicolon/period, ensure single space after
        cleaned = _RE_SPACE_COMMA.sub(", ", cleaned)
        cleaned = _RE_SPACE_SEMIC.sub("; ", cleaned)
        cleaned = _RE_SPACE_DOT.sub(". ", cleaned)
        # Collapse any remaining double+ spaces to single
        cleaned = _RE_DOUBLE_SPC.sub(" ", cleaned)
        cleaned = cleaned.strip()
        if cleaned:
            result_lines.append(cleaned)
    return "\n\n".join(result_lines)


# ---------------------------------------------------------------------------
# Built-in formatters (fallback when no template)
# ---------------------------------------------------------------------------


def format_jobs_list(response: dict) -> str:
    total, jobs = _extract_list_data(response, "jobs")
    rows = []
    for j in jobs:
        rows.append(
            [
                j.get("jobId", j.get("id", "")),
                j.get("status", ""),
                j.get("name", ""),
                j.get("appName", ""),
                j.get("queue", ""),
                j.get("owner", ""),
                j.get("slots", ""),
                j.get("submitTime", ""),
            ]
        )
    header = [
        "JOB_ID",
        "STATUS",
        "NAME",
        "APP",
        "QUEUE",
        "OWNER",
        "SLOTS",
        "SUBMIT_TIME",
    ]
    lines = [f"Total: {total}", "", _table(header, rows)]
    return "\n".join(lines)


def format_job_detail(response: dict) -> str:
    data = response.get("data", {})
    if isinstance(data, list):
        data = data[0] if data else {}
    if not data:
        return "(no data)"

    fields = [
        ("Job ID", data.get("jobId", data.get("id", ""))),
        ("Name", data.get("name", "")),
        ("Status", data.get("status", "")),
        ("Application", data.get("appName", "")),
        ("Queue", data.get("queue", "")),
        ("Owner", data.get("owner", data.get("userNameCn", ""))),
        ("Slots", data.get("slots", "")),
        ("Host", ", ".join(data.get("executionHost", [])) or data.get("host", "")),
        ("Submit Time", data.get("submitTime", "")),
        ("Start Time", data.get("executionTime", "")),
        ("End Time", data.get("terminationTime", "")),
        ("Working Dir", data.get("cwd", "")),
        ("Project", data.get("project", "")),
        ("GPU", data.get("gpuNum", 0)),
    ]

    for key, label in [
        ("reasons", "Reasons"),
        ("alarmInfo", "Alarm"),
        ("exceptionInfo", "Exception"),
    ]:
        val = data.get(key)
        if val:
            if isinstance(val, list):
                val = ", ".join(str(v) for v in val)
            fields.append((label, val))

    max_label = max(len(f[0]) for f in fields)
    lines = []
    for label, value in fields:
        if value is not None and value != "" and value != 0 and value != []:
            lines.append(f"  {label:<{max_label}} : {value}")
    return "\n".join(lines)


def format_sessions_list(response: dict) -> str:
    total, sessions = _extract_list_data(response)
    rows = []
    for s in sessions:
        rows.append(
            [
                s.get("id", s.get("session_id", "")),
                s.get("app_id", ""),
                s.get("owner", s.get("ownername", "")),
                s.get("host", ""),
                s.get("status", ""),
                s.get("createDate", ""),
            ]
        )
    header = ["SESSION_ID", "APP", "OWNER", "HOST", "STATUS", "CREATE_TIME"]
    lines = [f"Total: {total}", "", _table(header, rows)]
    return "\n".join(lines)


def format_files_list(response: dict) -> str:
    _, files = _extract_list_data(response)
    has_mode = any(f.get("mode") for f in files)
    rows = []
    for f in files:
        ftype = f.get("fileType", "")
        if ftype == "symlink":
            icon = "[L]"
        elif ftype == "directory":
            icon = "[D]"
        else:
            icon = "[F]"
        mode = f.get("mode", "")
        owner = f.get("owner") or f.get("uid", "")
        gid = f.get("gid", "")
        size = _format_size(f.get("size", 0))
        modified = f.get("ts") or f.get("modifiedDate", "")
        if has_mode:
            rows.append(
                [
                    mode,
                    f"{icon} {f.get('fileName', '')}",
                    owner,
                    gid,
                    size,
                    modified,
                ]
            )
        else:
            rows.append(
                [
                    f"{icon} {f.get('fileName', '')}",
                    owner,
                    size,
                    modified,
                ]
            )
    if has_mode:
        header = ["MODE", "NAME", "UID", "GID", "SIZE", "MODIFIED"]
        return _table(header, rows)
    header = ["NAME", "OWNER", "SIZE", "MODIFIED"]
    return _table(header, rows)


def format_apps_list(response: dict) -> str:
    _, apps = _extract_list_data(response)
    rows = []
    for a in apps:
        rows.append(
            [
                a.get("id", ""),
                a.get("name", ""),
                a.get("type", a.get("mode", "")),
                a.get("protocol", ""),
                a.get("os", ""),
            ]
        )
    header = ["APP_ID", "NAME", "TYPE", "PROTOCOL", "OS"]
    return f"Total: {len(apps)}\n\n" + _table(header, rows)


def format_departments(response: dict) -> str:
    data = response.get("data", [])
    if not data:
        return "(no data)"
    lines = []

    def walk(items, indent=0):
        for item in items:
            name = item.get("nameCn", item.get("name", ""))
            full_name = item.get("displayName", name)
            lines.append(f"{'  ' * indent}{full_name}")
            children = item.get("items", [])
            if children:
                walk(children, indent + 1)

    walk(data)
    return "\n".join(lines)


def format_users_list(response: dict) -> str:
    data = response.get("data", {})
    if isinstance(data, dict):
        total = data.get("totalCount", 0)
        users = data.get("list", [])
    else:
        users = data if isinstance(data, list) else []
        total = len(users)

    rows = []
    for u in users:
        rows.append(
            [
                u.get("userName", ""),
                u.get("userNameCn", ""),
                u.get("userDepNameCn", u.get("userDepName", "")),
                u.get("userStat", ""),
                u.get("userMail", ""),
            ]
        )
    header = ["USERNAME", "DISPLAY_NAME", "DEPARTMENT", "STATUS", "EMAIL"]
    lines = [f"Total: {total}", "", _table(header, rows)]
    return "\n".join(lines)


def format_generic(response: dict) -> str:
    """Generic formatter: tries to detect list/single data and format accordingly."""
    data = response.get("data")
    if data is None:
        return response.get("message", "(no data)")
    if isinstance(data, list):
        if not data:
            return "(empty list)"
        if isinstance(data[0], dict):
            headers = list(data[0].keys())[:8]
            rows = [[str(item.get(h, "")) for h in headers] for item in data[:50]]
            return f"Total: {len(data)}\n\n" + _table(headers, rows)
        return "\n".join(str(item) for item in data[:50])
    if isinstance(data, dict):
        lines = []
        for k, v in data.items():
            if v is not None and v != "" and v != [] and v != {}:
                if isinstance(v, (list, dict)):
                    v = json.dumps(v, ensure_ascii=False)
                lines.append(f"  {k}: {v}")
        return "\n".join(lines) if lines else "(empty)"
    return str(data)


def format_config_show(response: dict) -> str:
    """Format config show as a key-value detail view."""
    if not response or not isinstance(response, dict):
        return "(no data)"

    pairs = []
    for k, v in response.items():
        if v is None:
            continue
        if isinstance(v, (dict, list)):
            v = json.dumps(v, ensure_ascii=False)
        pairs.append((k, str(v)))

    if not pairs:
        return "(no data)"

    max_label = max(len(p[0]) for p in pairs)
    lines = []
    for label, value in pairs:
        lines.append(f"  {label:<{max_label}} : {value}")
    return "\n".join(lines)


def format_sessions_start(response: dict) -> str:
    """Format session start response with connection info."""
    data = response.get("data", [])
    if not data:
        return response.get("message", "(no data)")
    if isinstance(data, dict):
        data = [data]

    lines = []
    for item in data:
        session_id = item.get("session_id") or item.get("id", "")
        if session_id:
            lines.append(f"Session ID: {session_id}")
        app_id = item.get("app_id", "")
        if app_id:
            lines.append(f"Application: {app_id}")
        jhapp_url = item.get("jhappUrl", "")
        if jhapp_url:
            lines.append(f"JHApp URL: {jhapp_url}")
        desktop_id = item.get("desktopId", "")
        if desktop_id:
            lines.append(f"Desktop ID: {desktop_id}")
    if lines:
        return "\n".join(lines)
    return format_generic(response)


def format_job_submit(response: dict) -> str:
    """Format job submit response."""
    data = response.get("data")
    if data is None:
        msg = response.get("message", "")
        if msg:
            return msg
        return "(no data)"
    if isinstance(data, dict):
        job_id = data.get("jobId") or data.get("job_id") or data.get("id", "")
        if job_id:
            result = response.get("result", "")
            status = f" (result: {result})" if result else ""
            return f"Job submitted successfully, Job ID: {job_id}{status}"
        lines = []
        for k, v in data.items():
            if v is not None and v != "":
                lines.append(f"  {k}: {v}")
        return "\n".join(lines) if lines else str(data)
    return str(data)


def format_simple_result(response: dict) -> str:
    """Format simple success/failure result for mutation operations."""
    result = response.get("result", "")
    message = response.get("message", "")
    data = response.get("data")

    lines = []
    if result:
        lines.append(f"Result: {result}")
    if message:
        lines.append(f"Message: {message}")
    if data is not None:
        if isinstance(data, (dict, list)):
            lines.append(f"Data: {json.dumps(data, ensure_ascii=False)}")
        else:
            lines.append(f"Data: {data}")
    return "\n".join(lines) if lines else format_generic(response)


# ---------------------------------------------------------------------------
# Formatter registry
# ---------------------------------------------------------------------------

_FORMATTERS: Dict[str, Callable] = {
    "jobs.list": format_jobs_list,
    "jobs.status": format_jobs_list,
    "jobs.get": format_job_detail,
    "jobs.submit": format_job_submit,
    "jobs.stop": format_simple_result,
    "jobs.suspend": format_simple_result,
    "jobs.resume": format_simple_result,
    "jobs.delete": format_simple_result,
    "sessions.list": format_sessions_list,
    "sessions.list-all": format_sessions_list,
    "sessions.start": format_sessions_start,
    "sessions.connect": format_simple_result,
    "sessions.disconnect": format_simple_result,
    "sessions.close": format_simple_result,
    "sessions.share": format_simple_result,
    "files.list": format_files_list,
    "files.copy": format_simple_result,
    "files.rename": format_simple_result,
    "files.delete": format_simple_result,
    "files.mkdir": format_simple_result,
    "files.compress": format_simple_result,
    "files.uncompress": format_simple_result,
    "files.upload": format_simple_result,
    "files.download": format_simple_result,
    "files.conf": format_simple_result,
    "apps.list": format_apps_list,
    "departments.list": format_departments,
    "departments.create": format_simple_result,
    "departments.update": format_simple_result,
    "departments.delete": format_simple_result,
    "users.list": format_users_list,
    "users.create": format_simple_result,
    "users.update": format_simple_result,
    "users.delete": format_simple_result,
    "users.reset-password": format_simple_result,
    "config.show": format_config_show,
    "auth.login": format_simple_result,
    "auth.logout": format_simple_result,
    "auth.ping": format_simple_result,
}


def register_formatter(command: str, func: Callable) -> None:
    """Register a custom formatter function for a CLI command."""
    _FORMATTERS[command] = func


def _extract_template_fields(command: str, response: dict) -> dict:
    """
    Extract only fields defined in the template from the response.
    Returns a filtered dict suitable for JSON output.
    """
    template = get_template(command)
    if not template:
        return response

    t = template.get("type", "table")
    fields = template.get("fields", [])
    if not fields:
        return response

    if t == "table":
        # Extract items and filter fields
        items = _resolve_path(response, template.get("items_path", "data"))
        if items is None:
            return response
        if isinstance(items, dict):
            items = [items]
        if not isinstance(items, list):
            return response

        field_keys = [f["key"] for f in fields]
        filtered_items = []
        for item in items:
            filtered = {}
            for f in fields:
                val = _get_field_value(item, f)
                if val:
                    filtered[f.get("label", f["key"])] = val
            filtered_items.append(filtered)

        result = {"total": len(filtered_items), "items": filtered_items}
        total_key = template.get("total_key")
        if total_key:
            total = _resolve_path(response, total_key)
            if total is not None:
                result["total"] = total
        return result

    elif t == "detail":
        item = _resolve_path(response, template.get("item_path", "data"))
        if item is None:
            return response
        if isinstance(item, list):
            item = item[0] if item else {}
        if not isinstance(item, dict):
            return response

        filtered = {}
        for f in fields:
            val = _get_field_value(item, f)
            if val:
                filtered[f.get("label", f["key"])] = val
        return filtered

    elif t == "tree":
        # Tree format doesn't filter well to JSON, return data as-is
        items = _resolve_path(response, template.get("items_path", "data"))
        return {"data": items} if items else response

    return response


def format_output(command: str, response: dict, output_format: str = "table") -> str:
    """
    Format API response for CLI output.

    Resolution order:
    1. "raw"  — return original API response as JSON (no filtering)
    2. "json" — return template-filtered fields as JSON
    3. "table"/"text" — use template or built-in formatter for display

    Args:
        command: CLI command name (e.g., "jobs.list")
        response: Raw API response dict
        output_format: "raw", "json", "table", or "text"

    Returns:
        Formatted string
    """
    if output_format == "raw":
        return json.dumps(response, indent=2, ensure_ascii=False)

    if output_format == "json":
        filtered = _extract_template_fields(command, response)
        return json.dumps(filtered, indent=2, ensure_ascii=False)

    # Try template-driven formatting
    template = get_template(command)
    if template:
        try:
            t = template.get("type", "table")
            if t == "table":
                result = _format_table_template(template, response)
                if result:
                    return result
            elif t == "detail":
                result = _format_detail_template(template, response)
                if result:
                    return result
            elif t == "tree":
                result = _format_tree_template(template, response)
                if result:
                    return result
            elif t == "text":
                result = _format_text_template(template, response)
                if result:
                    return result
        except Exception:
            pass  # Fall through to built-in

    # Try registered formatter function
    formatter = _FORMATTERS.get(command)
    if formatter:
        try:
            return formatter(response)
        except Exception:
            pass

    # Fallback
    return format_generic(response)
