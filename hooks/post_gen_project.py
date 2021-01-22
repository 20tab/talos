#!/usr/bin/env python
"""Define hooks to be run after project generation."""

import json
import os  # noqa
import secrets
import sys  # noqa
from pathlib import Path

from cookiecutter.main import cookiecutter

try:
    import gitlab  # noqa
except ModuleNotFoundError:  # pragma: no cover
    pass


class MainProcess:
    """Main process class."""

    BACKEND_URL = "https://github.com/20tab/django-continuous-delivery"
    FRONTEND_URLS = {
        "None": "",
        "React": "https://github.com/20tab/react-continuous-delivery",
        "React (TypeScript)": "https://github.com/20tab/react-ts-continuous-delivery",
    }

    def __init__(self, *args, **kwargs):
        """Create a main process instance with chosen parameters."""
        cookiecutter_path = Path("cookiecutter.json")
        cookiecutter_dict = json.loads(cookiecutter_path.read_text())
        self.domain_url = cookiecutter_dict["domain_url"]
        self.gitlab_group_slug = cookiecutter_dict["gitlab_group_slug"]
        self.project_name = cookiecutter_dict["project_name"]
        self.project_slug = cookiecutter_dict["project_slug"]
        self.use_gitlab = cookiecutter_dict["use_gitlab"]
        self.use_media = cookiecutter_dict["use_media"]
        self.backend_url = self.BACKEND_URL
        self.frontend_url = self.FRONTEND_URLS[cookiecutter_dict["which_frontend"]]
        cookiecutter_dict["has_frontend"] = bool(self.frontend_url)
        cookiecutter_path.write_text(json.dumps(cookiecutter_dict, indent=2))

    def create_env_file(self):
        """Create env file from the template."""
        env_template = Path(".env_template").read_text()
        env_text = env_template.replace(
            "__SECRETKEY__", secrets.token_urlsafe(40)
        ).replace("__PASSWORD__", secrets.token_urlsafe(8))
        Path(".env").write_text(env_text)

    def copy_secrets(self):
        """Copy the Kubernetes secrets manifest."""
        secrets_template = ""
        environments = {
            "development": {
                "configuration": "Development",
                "debug": "False",
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
        secrets_template = Path("k8s/2_secrets.yaml_template").read_text()
        for environment, values in environments.items():
            secrets_text = (
                secrets_template.replace("__CONFIGURATION__", values["configuration"])
                .replace("__DEBUG__", values["debug"])
                .replace("__ENVIRONMENT__", environment)
                .replace("__SUBDOMAIN__", values["subdomain"])
                .replace("__SECRETKEY__", secrets.token_urlsafe(40))
                .replace("__PASSWORD__", secrets.token_urlsafe(8))
            )
            Path(f"k8s/{environment}/2_secrets.yaml").write_text(secrets_text)

    def create_subprojects(self):
        """Create subprojects."""
        cookiecutter(
            self.backend_url,
            extra_context={
                "database_url": (
                    f"postgres://postgres:postgres@postgres:5432/{self.project_slug}"
                ),
                "domain_url": self.domain_url,
                "gitlab_group_slug": self.gitlab_group_slug,
                "project_dirname": "backend",
                "project_name": self.project_name,
                "project_slug": self.project_slug,
                "use_media": self.use_media,
            },
            no_input=True,
        )
        if self.frontend_url:
            cookiecutter(
                self.frontend_url,
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
            exec(Path("./scripts/python/gitlab_sync.py").read_text())


if __name__ == "__main__":
    main_process = MainProcess()
    main_process.run()
