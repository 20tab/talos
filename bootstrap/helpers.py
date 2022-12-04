"""Web project initialization helpers."""

import json
from functools import partial
from time import time

import click
from slugify import slugify

from bootstrap.constants import DUMP_EXCLUDED_OPTIONS, DUMPS_DIR

error = partial(click.style, fg="red")

warning = partial(click.style, fg="yellow")


def format_gitlab_variable(value, masked=False, protected=True):
    """Format the given value to be used as a Terraform variable."""
    return (
        f'{{ value = "{value}"'
        + (masked and ", masked = true" or "")
        + (not protected and ", protected = false" or "")
        + "}"
    )


def format_tfvar(value, value_type=None):
    """Format the given value to be used as a Terraform variable."""
    if value_type == "list":
        return "[" + ", ".join(format_tfvar(i) for i in value) + "]"
    elif value_type == "bool":
        return value and "true" or "false"
    elif value_type == "num":
        return str(value)
    else:
        return f'"{value}"'


def dump_options(options):
    """Dump bootstrap options."""
    if click.confirm(
        warning("Would you like to dump the safe boostrap options?"),
    ):
        DUMPS_DIR.mkdir(exist_ok=True)
        dump_path = DUMPS_DIR / f"{time():.0f}.json"
        dump_path.write_text(
            json.dumps(
                {k: v for k, v in options.items() if k not in DUMP_EXCLUDED_OPTIONS},
                indent=2,
            )
        )


def load_options():
    """Load bootstrap options from a previous dump, if available."""
    try:
        dump_path = sorted(DUMPS_DIR.glob("*.json"))[-1]
    except IndexError:
        return {}
    else:
        if click.confirm(
            warning(f"A dump was found at '{dump_path}'. Would you like to load it?"),
        ):
            return json.load(dump_path.open())
        else:
            return {}


def slugify_option(ctx, param, value):
    """Slugify an option value."""
    return value and slugify(value)
