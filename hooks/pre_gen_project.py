#!/usr/bin/env python
"""
Define hooks to be run before project generation.

NOTE: OrderedDict is used by cookiecutter during jinja template render.
"""

import json
import os
import sys
from collections import OrderedDict  # noqa
from pathlib import Path

try:
    import gitlab  # noqa
except ModuleNotFoundError:  # pragma: no cover
    pass


class MainProcess:
    """Main process class."""

    TOKEN = "GITLAB_PRIVATE_TOKEN"
    URL = "https://gitlab.com"

    def __init__(self, *args, **kwargs):
        """Create a main process instance with chosen parameters."""
        self.project_name = "{{cookiecutter.project_name}}"
        self.project_slug = "{{cookiecutter.project_slug}}"
        self.group_slug = self.project_slug
        self.use_gitlab = "{{cookiecutter.use_gitlab}}" == "Yes"
        if self.use_gitlab:
            try:
                private_token = os.environ[self.TOKEN]
            except KeyError:
                sys.exit(f"The environment variable '{self.TOKEN}' is missing.")
            try:
                self.gl = gitlab.Gitlab(self.URL, private_token=private_token)
            except NameError:
                sys.exit("The 'python-gitlab' package is missing.")
            try:
                self.gl.auth()
            except gitlab.exceptions.GitlabAuthenticationError:
                sys.exit(f"The environment variable '{self.TOKEN}' is not correct.")

    def run(self):
        """Run main process."""
        configuration = {{cookiecutter}}  # noqa
        configuration["gitlab_group_slug"] = None
        configuration["use_gitlab"] = self.use_gitlab
        Path("cookiecutter.json").write_text(json.dumps(configuration, indent=2))


if __name__ == "__main__":
    main_process = MainProcess()
    main_process.run()
