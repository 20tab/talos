"""Define hooks to be run before project generation."""

import json
import os
import re
import unicodedata
from collections import OrderedDict  # noqa

from gitlab import Gitlab

# OrderedDict is used by cookiecutter during jinja template render


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


class MainProcess:
    """Main process class."""

    def __init__(self, *args, **kwargs):
        """Create a main process instance with chosen parameters."""
        self.project_name = "{{ cookiecutter.project_name }}"
        self.project_slug = "{{ cookiecutter.project_slug }}"
        self.group_slug = self.project_slug
        self.use_gitlab = "{{ cookiecutter.use_gitlab }}" == "Yes"
        self.gl = Gitlab(
            "https://gitlab.com", private_token=os.environ["GITLAB_PRIVATE_TOKEN"],
        )
        self.gl.auth()

    def is_group_slug_available(self, group_slug):
        """Tell if group name is available."""
        for p in self.gl.groups.list(search=self.group_slug):
            if p.path == group_slug:
                return False
        for u in self.gl.users.list(username=group_slug):
            if (
                u.web_url.replace("https://gitlab.com/", "").casefold()
                == group_slug.casefold()
            ):
                return False
        return True

    def set_gitlab_group_slug(self):
        """Set gitlab group name as slug."""
        group_slug = (
            input(f"Choose the gitlab group path slug [{self.group_slug}]: ")
            or self.group_slug
        )
        self.group_slug = slugify(group_slug)
        while len(self.group_slug) > 30:
            self.group_slug = slugify(
                input("Please choose a name shorter than 30 characters: ")
            )
        while not self.is_group_slug_available(self.group_slug):
            self.group_slug = input(
                f"A Gitlab group named '{self.group_slug}' already exists. "
                "Please choose a different name and try again: "
            )

    def run(self):
        """Run main process."""
        configuration = {{cookiecutter}}  # noqa
        configuration["gitlab_group_slug"] = None
        configuration["use_gitlab"] = self.use_gitlab
        if self.use_gitlab:
            self.set_gitlab_group_slug()
            configuration["gitlab_group_slug"] = self.group_slug

        with open("cookiecutter.json", "w+") as f:
            f.write(json.dumps(configuration, indent=2))

if __name__ == "__main__":
    main_process = MainProcess()
    main_process.run()
