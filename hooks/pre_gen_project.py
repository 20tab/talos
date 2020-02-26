"""Define hooks to be run before project generation."""

import json


def save_cookiecutter_conf(self):
    """Save cookiecutter configuration inside the project."""
    with open("cookiecutter.json", "w+") as f:
        f.write(json.dumps({{cookiecutter}}, indent=2))  # noqa
