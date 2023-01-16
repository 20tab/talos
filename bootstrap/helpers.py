"""Web project initialization helpers."""

import json
import re
from functools import partial
from pathlib import Path
from time import time

import click
import validators
from slugify import slugify

from bootstrap.constants import DUMP_EXCLUDED_OPTIONS, DUMPS_DIR

error = partial(click.style, fg="red")

warning = partial(click.style, fg="yellow")


class CollectorJSONEncoder(json.JSONEncoder):
    """A JSON encoder supporting bootstrap collector options types."""

    def default(self, o):
        """Perform default serialization."""
        if isinstance(o, Path):
            return str(o.resolve())
        return super().default(o)


def format_gitlab_variable(value, masked=False, protected=True):
    """Format the given value to be used as a GitLab variable."""
    return (
        f'{{ value = "{value}"'
        + (masked and ", masked = true" or "")
        + (not protected and ", protected = false" or "")
        + " }"
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
                cls=CollectorJSONEncoder,
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
    """Slugify a click option value."""
    return value and slugify(value)


def validate_or_prompt_domain(message, value=None, default=None, required=True):
    """Validate the given domain or prompt until a valid value is provided."""
    if value is None:
        value = click.prompt(message, default=default)
    if not required and value == "" or validators.domain(value):
        return value
    click.echo(error("Please type a valid domain!"))
    return validate_or_prompt_domain(message, None, default, required)


def validate_or_prompt_email(message, value=None, default=None, required=True):
    """Validate the given email address or prompt until a valid value is provided."""
    if value is None:
        value = click.prompt(message, default=default)
    if not required and value == "" or validators.email(value):
        return value
    click.echo(error("Please type a valid email!"))
    return validate_or_prompt_email(message, None, default, required)


def validate_or_prompt_secret(message, value=None, default=None, required=True):
    """Validate the given secret or prompt until a valid value is provided."""
    if value is None:
        value = click.prompt(message, default=default, hide_input=True)
    if not required and value == "" or validators.length(value, min=8):
        return value
    click.echo(error("Please type at least 8 chars!"))
    return validate_or_prompt_secret(message, None, default, required)


def validate_or_prompt_path(message, value=None, default=None, required=True):
    """Validate the given path or prompt until a valid path is provided."""
    if value is None:
        value = click.prompt(message, default=default)
    if (
        not required
        and value == ""
        or re.match(r"^(?:/?[\w_\-]+)(?:\/[\w_\-]+)*\/?$", value)
    ):
        return value
    click.echo(
        error(
            "Please type a valid slash-separated path containing letters, digits, "
            "dashes and underscores!"
        )
    )
    return validate_or_prompt_path(message, None, default, required)


def validate_or_prompt_url(message, value=None, default=None, required=True):
    """Validate the given URL or prompt until a valid value is provided."""
    if value is None:
        value = click.prompt(message, default=default)
    if not required and value == "" or validators.url(value):
        return value.rstrip("/")
    click.echo(error("Please type a valid URL!"))
    return validate_or_prompt_url(message, None, default, required)
