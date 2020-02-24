import json
import re
import unicodedata

from collections import OrderedDict # noqa


def update_cookiecutter_conf(key, value):
    """Update cookiecutter configuration file."""
    conf = {}
    with open("cookiecutter.json", "r") as f:
        conf = json.loads(f.read())
    with open("cookiecutter.json", "w+") as f:
        conf[key] = value
        f.write(json.dumps(conf, indent=2))


def get_cookiecutter_conf():
    """Get cookiecutter configuration."""
    with open("cookiecutter.json", "r") as f:
        return json.loads(f.read())


def slugify(value):
    """
    Transofrm text into slug.

    Convert to ASCII.
    Convert spaces to hyphens.
    Remove characters that aren't alphanumerics, underscores, or hyphens.
    Convert to lowercase.
    Also strip leading and trailing whitespace.
    """
    value = str(value)
    value = (
        unicodedata.normalize("NFKD", str(value))
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    value = re.sub(r"[^\w\s-]", "", value.casefold()).strip()
    return re.sub(r"[-\s]+", "-", value)
