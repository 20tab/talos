"""Define hooks to be run after project generation."""

import json
import subprocess

from cookiecutter.main import cookiecutter


def get_cookiecutter_conf():
    """Get cookiecutter configuration."""
    with open("cookiecutter.json", "r") as f:
        return json.loads(f.read())


class MainProcess:
    """Main process class."""

    def __init__(self, *args, **kwargs):
        """Create a main process instance with chosen parameters."""
        cookiecutter_conf = get_cookiecutter_conf()
        self.domain_url = cookiecutter_conf["domain_url"]
        self.gitlab_group_slug = cookiecutter_conf["gitlab_group_slug"]
        self.project_name = cookiecutter_conf["project_name"]
        self.project_slug = cookiecutter_conf["project_slug"]
        self.use_gitlab = cookiecutter_conf["use_gitlab"]
        self.use_media_volume = cookiecutter_conf["use_media_volume"]

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
        with open("k8s/2_secrets.yaml.tpl", "r") as f:
            secrets_template = f.read()
        for environment, values in environments.items():
            secrets = (
                secrets_template.replace("__CONFIGURATION__", values["configuration"])
                .replace("__DEBUG__", values["debug"])
                .replace("__ENVIRONMENT__", environment)
                .replace("__SUBDOMAIN__", values["subdomain"])
            )
            with open(f"k8s/{environment}/2_secrets.yaml", "w+") as fd:
                fd.write(secrets)

    def create_subprojects(self):
        """Create the the django and react apps."""
        subprocess.run("./scripts/init.sh")
        cookiecutter(
            # "https://github.com/20tab/django-continuous-delivery",
            "/Users/rafleze/projects/django-continuous-delivery",
            extra_context={
                "domain_url": self.domain_url,
                "gitlab_group_slug": self.gitlab_group_slug,
                "project_dirname": "backend",
                "project_name": self.project_name,
                "project_slug": self.project_slug,
                "use_media_volume": self.use_media_volume
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
        self.copy_secrets()
        self.create_subprojects()
        if self.use_gitlab:
            subprocess.run("./scripts/gitlab_sync.sh")


if __name__ == "__main__":
    main_process = MainProcess()
    main_process.run()
