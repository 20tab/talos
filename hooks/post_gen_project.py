#!/usr/bin/env python
"""Define hooks to be run after project generation."""

import json
import subprocess
from pathlib import Path
from shutil import copyfile

from cookiecutter.main import cookiecutter


class MainProcess:
    """Main process class."""

    def __init__(self, *args, **kwargs):
        """Create a main process instance with chosen parameters."""
        cookiecutter_conf = json.loads(Path("cookiecutter.json").read_text())
        self.domain_url = cookiecutter_conf["domain_url"]
        self.gitlab_group_slug = cookiecutter_conf["gitlab_group_slug"]
        self.project_name = cookiecutter_conf["project_name"]
        self.project_slug = cookiecutter_conf["project_slug"]
        self.use_gitlab = cookiecutter_conf["use_gitlab"]
        self.use_media_volume = cookiecutter_conf["use_media_volume"]

    def create_env_file(self):
        """Create env file from the template."""
        copyfile(Path(".env.tpl"), Path(".env"))

    def copy_secrets(self):
        """Copy the Kubernetes secrets manifest."""
        secrets_template = ""
        environments = {
            "development": {
                "configuration": "Development",
                "debug": "True",
                "subdomain": "dev",
            },
            "integration": {
                "configuration": "Integration",
                "debug": "False",
                "subdomain": "test",
            },
            "production": {
                "configuration": "Production",
                "debug": "False",
                "subdomain": "www",
            },
        }
        secrets_template = Path("k8s/2_secrets.yaml.tpl").read_text()
        for environment, values in environments.items():
            secrets = (
                secrets_template.replace("__CONFIGURATION__", values["configuration"])
                .replace("__DEBUG__", values["debug"])
                .replace("__ENVIRONMENT__", environment)
                .replace("__SUBDOMAIN__", values["subdomain"])
            )
            Path(f"k8s/{environment}/2_secrets.yaml").write_text(secrets)

    def create_subprojects(self):
        """Create the the django and react apps."""
        cookiecutter(
            "https://github.com/20tab/django-continuous-delivery",
            extra_context={
                "domain_url": self.domain_url,
                "gitlab_group_slug": self.gitlab_group_slug,
                "project_dirname": "backend",
                "project_name": self.project_name,
                "project_slug": self.project_slug,
                "use_media_volume": self.use_media_volume,
            },
            no_input=True,
        )
        cookiecutter(
            "https://github.com/20tab/react-continuous-delivery",
            extra_context={
                "gitlab_group_slug": self.gitlab_group_slug,
                "project_dirname": "frontend",
                "project_name": self.project_name,
                "project_slug": self.project_slug,
            },
            no_input=True,
        )

    def run(self):
        """Run the main process operations."""
        self.create_env_file()
        self.copy_secrets()
        self.create_subprojects()
        if self.use_gitlab:
            subprocess.run("./scripts/gitlab_sync.sh")


if __name__ == "__main__":
    main_process = MainProcess()
    main_process.run()
