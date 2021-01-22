#!/usr/bin/env python3
"""Define GitLab class and utilities."""

import json
import os
import sys
from pathlib import Path

import gitlab


class GitlabSync:
    """A GitLab interface."""

    COOKIECUTTER = "cookiecutter.json"
    TOKEN = "GITLAB_PRIVATE_TOKEN"
    URL = "https://gitlab.com"

    def __init__(self, *args, **kwargs):
        """Initialize the instance."""
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
        cookiecutter_path = Path(self.COOKIECUTTER)
        cookiecutter_dict = json.loads(cookiecutter_path.read_text())
        try:
            self.group_slug = cookiecutter_dict["gitlab_group_slug"]
            self.project_slug = cookiecutter_dict["project_slug"]
            self.project_name = cookiecutter_dict["project_name"]
            self.has_frontend = cookiecutter_dict["has_frontend"]
        except KeyError:
            sys.exit(f"File {cookiecutter_path} is empty or incomplete.")

    def get_group(self):
        """Get gitlab group."""
        for p in self.gl.groups.list(search=self.group_slug):
            if p.path == self.group_slug:
                return p
        return None

    def create_group(self):
        """Create a GitLab group and sub-projects with badges."""
        self.group = self.gl.groups.create(
            {"name": self.project_name, "path": self.group_slug}
        )
        self.orchestrator = self.gl.projects.create(
            {"name": "Orchestrator", "namespace_id": self.group.id}
        )
        self.backend = self.gl.projects.create(
            {"name": "Backend", "namespace_id": self.group.id}
        )
        if self.has_frontend:
            self.frontend = self.gl.projects.create(
                {"name": "Frontend", "namespace_id": self.group.id}
            )
        self.group.badges.create(
            {
                "link_url": f"{self.URL}/" "%{project_path}/pipelines",
                "image_url": (
                    f"{self.URL}"
                    "/%{project_path}/badges/%{default_branch}/pipeline.svg"
                ),
            }
        )
        self.group.badges.create(
            {
                "link_url": f"https://{self.group.path}.gitlab.io/{self.backend.path}",
                "image_url": (
                    f"{self.URL}"
                    "/%{project_path}/badges/%{default_branch}/coverage.svg"
                ),
            }
        )

    def set_default_branch(self):
        """Set default branch."""
        self.orchestrator.default_branch = "develop"
        self.orchestrator.save()
        self.backend.default_branch = "develop"
        self.backend.save()
        if self.has_frontend:
            self.frontend.default_branch = "develop"
            self.frontend.save()

    def set_owners(self):
        """Add given Gitlab usernames as owner to the gitlab group."""
        owners = input(
            "Insert a comma separated list of usernames to set as group owners: "
        )
        for owner in owners.split(","):
            try:
                user = self.gl.users.list(username=owner.strip())[0]
            except IndexError:
                print(f"Username '{owner}' doesn't exists. Please add him in Gitlab.")
            else:
                self.group.members.create(
                    {"user_id": user.id, "access_level": gitlab.OWNER_ACCESS}
                )
                print(f"Owner '{owner}' added to group '{self.group.name}'.")

    def set_members(self):
        """Add given Gitlab usernames as mantainer to the gitlab group."""
        members = input(
            "Insert a comma separated list of usernames to set as group mantainers: "
        )
        for member in members.split(","):
            try:
                user = self.gl.users.list(username=member.strip())[0]
            except IndexError:
                print(f"Username '{member}' doesn't exists. Please add him in Gitlab.")
            else:
                self.group.members.create(
                    {"user_id": user.id, "access_level": gitlab.MAINTAINER_ACCESS}
                )
                print(f"Member '{member}' added to group '{self.group.name}'.")

    def git_init(self):
        """Initialize local git repository."""
        os.system(f"./scripts/git_init.sh {self.orchestrator.ssh_url_to_repo}")
        os.system(
            "cd backend && ../scripts/git_init.sh " f"{self.backend.ssh_url_to_repo}"
        )
        if self.has_frontend:
            os.system(
                "cd frontend && ../scripts/git_init.sh "
                f"{self.frontend.ssh_url_to_repo}"
            )

    def update_readme(self):
        """Update README.md replacing the Gitlab group placeholder with group slug."""
        readme_path = Path("README.md")
        readme_text = readme_path.read_text()
        readme_text = readme_text.replace("__GITLAB_GROUP__", self.group_slug)
        readme_path.write_text(readme_text)

    def run(self):
        """Run the main process operations."""
        self.update_readme()
        self.create_group()
        self.git_init()
        self.set_default_branch()
        self.set_owners()
        self.set_members()


if __name__ == "__main__":
    gl = GitlabSync()
    gl.run()
