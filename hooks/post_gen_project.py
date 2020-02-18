"""Define hooks to be run after project generation."""

import os
import requests
import shutil

from cookiecutter.main import cookiecutter
from gitlab import Gitlab, MAINTAINER_ACCESS


class GitlabSync:
    """A GitLab interface."""

    def __init__(self, *args, **kwargs):
        """Initialize the instance."""
        self.protocol = "https://"
        self.server_url = "gitlab.com"
        self.gl = Gitlab(
           f"{self.protocol}{self.server_url}" , private_token=os.environ["GITLAB_PRIVATE_TOKEN"]
        )
        self.gl.auth()

    def is_group_name_available(self, group_name):
        """Tell if group name is available."""
        resp = requests.get(f"{self.protocol}{self.server_url}")
        for p in self.gl.groups.list(search=group_name):
            if p.path == group_name:
                return False
        for u in self.gl.users.list(username=group_name):
            if u.web_url.replace(f"{self.protocol}{self.server_url}/", "").casefold() == group_name.casefold():
                return False
        return True

    def create_group(self, project_name, group_name):
        """Create a GitLab group."""
        self.group = self.gl.groups.create({"name": project_name, "path": group_name})
        pipeline_badge_link = "/%{project_path}/pipelines"
        pipeline_badge_image_url = "/%{project_path}/badges/%{default_branch}/pipeline.svg"
        pipeline_badge = self.group.badges.create({
            "link_url": f"{self.protocol}{self.server_url}{pipeline_badge_link}", 
            'image_url': f"{self.protocol}{self.server_url}{pipeline_badge_image_url}"
        })
        self.orchestrator = self.gl.projects.create(  # noqa
            {"name": "Orchestrator", "namespace_id": self.group.id}
        )
        self.backend = self.gl.projects.create(  # noqa
            {"name": "Backend", "namespace_id": self.group.id}
        )
        coverage_badge_image_url = "/%{project_path}/badges/%{default_branch}/coverage.svg"
        coverage_badge = self.group.badges.create({
            "link_url": f"{self.protocol}{self.group.path}.{self.server_url}/{self.backend.path}", 
            'image_url': f"{self.protocol}{self.server_url}{coverage_badge_image_url}"
        })
        self.frontend = self.gl.projects.create(  # noqa
            {"name": "Frontend", "namespace_id": self.group.id}
        )

    def set_default_branch(self):
        """Set default branch"""
        self.orchestrator.default_branch = "develop"
        self.orchestrator.save()
        self.backend.default_branch = "develop"
        self.backend.save()
        self.frontend.default_branch = "develop"
        self.frontend.save()

    def set_members(self):
        """Add given members to gitlab group"""
        members = input("Insert the usernames of all users you want to add to the group, separated by comma or empty to skip: ")
        for member in members.split(","):
            try:
                user = self.gl.users.list(username=member.strip())[0]
                self.group.members.create({'user_id': user.id, 'access_level': MAINTAINER_ACCESS})
                print(f"{member} added to group {self.group.name}")
            except IndexError:
                print(f"{member} doesn't exists. Please add him from gitlab.com")


class MainProcess:
    """Main process class"""

    def __init__(self, *args, **kwargs):
        """Create a main process instance with chosen parameters"""
        self.project_name = "{{ cookiecutter.project_name }}"
        self.project_slug = "{{ cookiecutter.project_slug }}"
        self.group_name = self.project_slug
        self.use_gitlab = "{{ cookiecutter.use_gitlab }}" == "y"
        self.gitlab = None
        
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

    def create_subprojects(self):
        """Create the the django and react apps."""
        os.system("./bin/init.sh")
        cookiecutter(
            "https://github.com/20tab/django-continuous-delivery",
            extra_context={
                "project_name": self.project_name,
                "project_slug": self.project_slug,
                "project_dirname": "backend",
                "gitlab_group_name": self.group_name,
                "static_url": "/backendstatic/",
            },
            no_input=True,
        )
        cookiecutter(
            "https://github.com/20tab/react-continuous-delivery",
            extra_context={
                "project_name": self.project_name,
                "project_slug": self.project_slug,
                "gitlab_group_name": self.group_name,
                "project_dirname": "frontend",
            },
            no_input=True,
        )

    def git_init(self):
        """Initialize local git repository"""
        os.system(f"./bin/git_init.sh {self.gitlab.orchestrator.ssh_url_to_repo}")
        os.system(f"cd backend && ../bin/git_init.sh {self.gitlab.backend.ssh_url_to_repo}")
        os.system(f"cd frontend && ../bin/git_init.sh {self.gitlab.frontend.ssh_url_to_repo}")
    
    def run(self):
        # """Run the main process operations"""
        if self.use_gitlab:
            self.gitlab = GitlabSync()
            self.group_name = input(f"Choose the gitlab group name [{self.group_name}]: ") or self.group_name
            while not self.gitlab.is_group_name_available(self.group_name):
                self.group_name = input(
                    f'A Gitlab group named "{self.group_name}" already exists. Please choose a '
                    "different name and try again: "
                )
            self.gitlab.create_group(self.project_name, self.group_name)

        self.copy_secrets()
        self.create_subprojects()
        if self.gitlab:
            self.gitlab.set_members()
            self.git_init()
            self.gitlab.set_default_branch()


main_process = MainProcess()
main_process.run()