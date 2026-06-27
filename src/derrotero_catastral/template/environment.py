"""Sandboxed Jinja2 environment with custom derrotero filters.

Creates a :class:`jinja2.sandbox.SandboxedEnvironment` with:

* A two-directory loader chain (user path overrides built-in).
* A restricted Python-builtins whitelist for safe template execution.
* All custom filters registered (``to_dms``, ``to_quadrant``,
  ``format_number``, ``to_cardinal``).
"""


from jinja2 import FileSystemLoader
from jinja2.sandbox import SandboxedEnvironment

from derrotero_catastral.template.filters import (
    format_number,
    to_cardinal,
    to_dms,
    to_quadrant,
)

# ---------------------------------------------------------------------------
# Builtins whitelist — only these Python builtins are available in templates
# ---------------------------------------------------------------------------

ALLOWED_BUILTINS: list[str] = [
    "range",
    "dict",
    "list",
    "str",
    "int",
    "float",
    "bool",
    "enumerate",
    "zip",
    "len",
]

# ---------------------------------------------------------------------------
# Custom filter registry
# ---------------------------------------------------------------------------

_FILTERS: dict[str, callable] = {
    "format_number": format_number,
    "to_dms": to_dms,
    "to_quadrant": to_quadrant,
    "to_cardinal": to_cardinal,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def create_environment(
    builtin_dir: str | None = None,
    user_dir: str | None = None,
) -> SandboxedEnvironment:
    """Create a sandboxed Jinja2 environment for rendering derrotero templates.

    Parameters
    ----------
    builtin_dir
        Absolute path to the built-in templates directory (fallback).
        When ``None``, only *user_dir* (if set) is used.
    user_dir
        Absolute path to the user-provided templates directory (priority).
        When ``None``, only *builtin_dir* (if set) is used.

    Returns
    -------
    SandboxedEnvironment
        Configured environment ready for ``render()``.

    Raises
    ------
    ValueError
        When both *builtin_dir* and *user_dir* are ``None``.
    """
    if builtin_dir is None and user_dir is None:
        raise ValueError(
            "At least one of builtin_dir or user_dir must be provided"
        )

    # Build search paths — user takes precedence over built-in
    searchpaths: list[str] = []
    if user_dir is not None:
        searchpaths.append(user_dir)
    if builtin_dir is not None:
        searchpaths.append(builtin_dir)

    loader = FileSystemLoader(searchpaths)

    env = SandboxedEnvironment(
        loader=loader,
        autoescape=False,  # derroteros are plain text, not HTML
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Restrict builtins to the whitelist (class attribute override)
    env.builtins = list(ALLOWED_BUILTINS)

    # Register custom filters
    env.filters.update(_FILTERS)

    return env
