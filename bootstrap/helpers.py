#!/usr/bin/env python
"""Web project initialization cli helpers."""

import click
import validators
from slugify import slugify


def slugify_option(ctx, param, value):
    """Slugify an option value."""
    return value and slugify(value)


def validate_or_prompt_url(value, message, default=None, required=False):
    """Validate the given URL or prompt until a valid value is provided."""
    if value is not None:
        if not required and value == "" or validators.url(value):
            return value.strip("/")
        else:
            click.echo("Please type a valid URL!")
    new_value = click.prompt(message, default=default)
    return validate_or_prompt_url(new_value, message, default, required)


def validate_or_prompt_password(value, message, default=None, required=False):
    """Validate the given password or prompt until a valid value is provided."""
    if value is not None:
        if not required and value == "" or validators.length(value, min=8):
            return value
        else:
            click.echo("Please type at least 8 chars!")
    new_value = click.prompt(message, default=default, hide_input=True)
    return validate_or_prompt_password(new_value, message, default, required)
