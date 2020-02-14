"""Define hooks to be run before project generation."""

import os
import sys

from gitlab import Gitlab


class GitlabSync:
    """A GitLab interface."""

    def __init__(self, *args, **kwargs):
        """Initialize the instance."""
        self.gl = Gitlab(
            "https://gitlab.com", private_token=os.environ["GITLAB_PRIVATE_TOKEN"]
        )
        self.gl.auth()

    def is_group_name_available(self, group_name):
        """Tell if group name is available."""
        for p in self.gl.groups.list(search=group_name):
            if p.path == group_name:
                return False
        return True


gls = GitlabSync()
group_name = "{{ cookiecutter.gitlab_group}}"
if not gls.is_group_name_available(group_name):
    print(
        f"A Gitlab group named \"{group_name}\" already exists. Please choose a "
        "different name and try again."
    )
    sys.exit(1)
