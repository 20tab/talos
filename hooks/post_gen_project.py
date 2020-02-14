"""Define hooks to be run after project generation."""

import os
import shutil

from cookiecutter.main import cookiecutter
from gitlab import Gitlab


def remove(path):
    """Remove a file or a directory at the given path."""
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)


def copy_secrets():
    """Copy the Kubernetes secrets manifest."""
    with open("k8s/secrets.yaml.tpl", "r") as f:
        text = f.read()
        text_development = text.replace("__ENVIRONMENT__", "development")
        text_integration = text.replace("__ENVIRONMENT__", "integration")
        text_production = text.replace("__ENVIRONMENT__", "production")

        with open("k8s/development/secrets.yaml", "w+") as fd:
            fd.write(text_development)

        with open("k8s/integration/secrets.yaml", "w+") as fd:
            fd.write(text_integration)

        with open("k8s/production/secrets.yaml", "w+") as fd:
            fd.write(text_production)


def create_apps():
    """Create the the django and react apps."""
    os.system("./bin/init.sh")
    cookiecutter(
        "https://github.com/20tab/django-continuous-delivery",
        extra_context={
            "project_name": "{{cookiecutter.project_name}}",
            "project_slug": "{{cookiecutter.project_slug}}",
            "project_dirname": "backend",
            "static_url": "/backendstatic/",
        },
        no_input=True,
    )
    cookiecutter(
        "https://github.com/20tab/react-continuous-delivery",
        extra_context={
            "project_name": "{{cookiecutter.project_name}}",
            "project_slug": "{{cookiecutter.project_slug}}",
            "project_dirname": "frontend",
        },
        no_input=True,
    )


class GitlabSync:
    """A GitLab interface."""

    def __init__(self, *args, **kwargs):
        """Initialize the instance."""
        self.gl = Gitlab(
            "https://gitlab.com", private_token=os.environ["GITLAB_PRIVATE_TOKEN"]
        )
        self.gl.auth()

    def create_group(self, project_name, group_name):
        """Create a GitLab group."""
        group = self.gl.groups.create({"name": project_name, "path": group_name})
        orchestrator = self.gl.projects.create(  # noqa
            {"name": "Orchestrator", "namespace_id": group.id}
        )
        backend = self.gl.projects.create(  # noqa
            {"name": "Backend", "namespace_id": group.id}
        )
        frontend = self.gl.projects.create(  # noqa
            {"name": "Frontend", "namespace_id": group.id}
        )


gl = GitlabSync()
gl.create_group("{{ cookiecutter.project_name }}", "{{ cookiecutter.gitlab_group }}")

copy_secrets()
create_apps()
