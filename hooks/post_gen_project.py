# cat post_gen_project.py
from gitlab import Gitlab
import os
import sys
import shutil
from cookiecutter.main import cookiecutter


def remove(filepath):
    if os.path.isfile(filepath):
        os.remove(filepath)
    elif os.path.isdir(filepath):
        shutil.rmtree(filepath)


def copy_secrets():

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
    os.system("./bin/init.sh")
    cookiecutter(
        "https://github.com/20tab/django-continuous-delivery",
        extra_context={
            "project_name": "{{cookiecutter.project_name}}",
            "static_url": "/backendstatic/",
        },
        no_input=True,
    )
    cookiecutter(
        "https://github.com/20tab/react-continuous-delivery",
        extra_context={"project_name": "{{cookiecutter.project_name}}"},
        no_input=True,
    )


class GitlabSync:
    def __init__(self, *args, **kwargs):
        self.gl = Gitlab(
            "https://gitlab.com", private_token=os.environ["GITLAB_PRIVATE_TOKEN"]
        )
        self.gl.auth()

    def create_group(self, project_name, group_name):
        group = self.gl.groups.create({"name": project_name, "path": group_name})
        orchestrator = self.gl.projects.create(
            {"name": "Orchestrator", "namespace_id": group.id}
        )
        backend = self.gl.projects.create({"name": "Backend", "namespace_id": group.id})
        frontend = self.gl.projects.create(
            {"name": "Frontend", "namespace_id": group.id}
        )


gl = GitlabSync()
gl.create_group("{{ cookiecutter.project_name }}", "{{ cookiecutter.gitlab_group }}")

copy_secrets()
create_apps()
