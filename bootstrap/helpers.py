"""Web project initialization helpers."""

from slugify import slugify


def slugify_option(ctx, param, value):
    """Slugify an option value."""
    return value and slugify(value)
