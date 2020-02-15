"""Define hooks to be run after project generation."""

import os
import requests
import shutil

from cookiecutter.main import cookiecutter
from gitlab import Gitlab


class GitlabSync:
    """A GitLab interface."""

    def __init__(self, *args, **kwargs):
        """Initialize the instance."""
        self.server_url = "https://gitlab.com"
        self.gl = Gitlab(
           self.server_url , private_token=os.environ["GITLAB_PRIVATE_TOKEN"]
        )
        self.gl.auth()

    def is_group_name_available(self, group_name):
        """Tell if group name is available."""
        resp = requests.get(self.server_url)
        for p in self.gl.groups.list(search=group_name):
            if p.path == group_name:
                return False
        return True

    def create_group(self, project_name, group_name):
        """Create a GitLab group."""
        # TODO: check if group name == any account name because group creation will fail
        self.group = self.gl.groups.create({"name": project_name, "path": group_name})
        badge_link = "/%{project_path}/pipelines"
        badge_image_url = "/%{project_path}/badges/%{default_branch}/pipeline.svg"
        badge = self.group.badges.create({
            "link_url": f"{self.server_url}{badge_link}", 'image_url': f"{self.server_url}{badge_image_url}"
        })
        self.orchestrator = self.gl.projects.create(  # noqa
            {"name": "Orchestrator", "namespace_id": self.group.id}
        )
        self.backend = self.gl.projects.create(  # noqa
            {"name": "Backend", "namespace_id": self.group.id}
        )
        self.frontend = self.gl.projects.create(  # noqa
            {"name": "Frontend", "namespace_id": self.group.id}
        )

class MainProcess:
    """Main process class"""

    def __init__(self, *args, **kwargs):
        """Create a main process instance with chosen parameters"""
        self.project_name = "{{ cookiecutter.project_name }}"
        self.project_slug = "{{ cookiecutter.project_slug }}"
        self.use_gitlab = "{{ cookiecutter.use_gitlab }}" == "y"
        
    def remove(self, path):
        """Remove a file or a directory at the given path."""
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)

    def copy_secrets(self):
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

    def create_apps(self):
        """Create the the django and react apps."""
        os.system("./bin/init.sh")
        cookiecutter(
            "https://github.com/20tab/django-continuous-delivery",
            extra_context={
                "project_name": self.project_name,
                "project_slug": self.project_slug,
                "project_dirname": "backend",
                "static_url": "/backendstatic/",
            },
            no_input=True,
        )
        cookiecutter(
            "https://github.com/20tab/react-continuous-delivery",
            extra_context={
                "project_name": self.project_name,
                "project_slug": self.project_slug,
                "project_dirname": "frontend",
            },
            no_input=True,
        )

    def git_init(self):
        """Initialize local git repository"""
        os.system(".bin/gitinit.sh")
    
    def run(self):
        """Run the main process operations"""
        # if self.use_gitlab:
        #     gl = GitlabSync()
        #     self.group_name = input("Choose the gitlab group name: ")
        #     while not gl.is_group_name_available(self.group_name):
        #         self.group_name = input(
        #             f'A Gitlab group named "{self.group_name}" already exists. Please choose a '
        #             "different name and try again: "
        #         )
        #     gl.create_group(self.project_name, self.group_name)

        self.copy_secrets()
        self.create_apps()
        self.git_init()


main_process = MainProcess()
main_process.run()