"""Web project initialization helpers."""

from slugify import slugify


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


def slugify_option(ctx, param, value):
    """Slugify an option value."""
    return value and slugify(value)
