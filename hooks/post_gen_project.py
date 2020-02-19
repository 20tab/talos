"""Define hooks to be run after project generation."""

import json
import os
import shutil
import subprocess
import warnings

from collections import OrderedDict

from cookiecutter.main import cookiecutter


class MainProcess:
    """Main process class."""

    def __init__(self, *args, **kwargs):
        """Create a main process instance with chosen parameters."""
        self.project_name = "{{ cookiecutter.project_name }}"
        self.project_slug = "{{ cookiecutter.project_slug }}"
        self.group_slug = self.project_slug
        self.use_gitlab = "{{ cookiecutter.use_gitlab }}" == "Yes"
        self.gitlab = None

    def save_cookiecutter_conf(self):
        """Save cookiecutter configuration inside the project"""
        conf = {{cookiecutter}}
        with open("cookiecutter.json", "w+") as f:
            f.write(json.dumps(conf, indent=2))

    def remove(self, path):
        """Remove a file or a directory at the given path."""
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)

    def copy_secrets(self):
        """Copy the Kubernetes secrets manifest."""
        with open("k8s/2_secrets.yaml.tpl", "r") as f:
            text = f.read()
            text_development = text.replace("__ENVIRONMENT__", "development")
            text_integration = text.replace("__ENVIRONMENT__", "integration")
            text_production = text.replace("__ENVIRONMENT__", "production")

            with open("k8s/development/2_secrets.yaml", "w+") as fd:
                fd.write(text_development)

            with open("k8s/integration/2_secrets.yaml", "w+") as fd:
                fd.write(text_integration)

            with open("k8s/production/2_secrets.yaml", "w+") as fd:
                fd.write(text_production)

    def create_subprojects(self):
        """Create the the django and react apps."""
        subprocess.run("./scripts/init.sh")
        cookiecutter(
            "https://github.com/20tab/django-continuous-delivery",
            extra_context={
                "project_name": self.project_name,
                "project_slug": self.project_slug,
                "project_dirname": "backend",
                "gitlab_group_slug": self.group_slug,
                "static_url": "/backendstatic/",
            },
            no_input=True,
        )
        cookiecutter(
            "https://github.com/20tab/react-continuous-delivery",
            extra_context={
                "project_name": self.project_name,
                "project_slug": self.project_slug,
                "gitlab_group_slug": self.group_slug,
                "project_dirname": "frontend",
            },
            no_input=True,
        )

    def run(self):
        """Run the main process operations."""
        self.save_cookiecutter_conf()
        self.copy_secrets()
        self.create_subprojects()
        if self.use_gitlab:
            subprocess.run("./scripts/gitlab_sync.sh")


main_process = MainProcess()
main_process.run()
