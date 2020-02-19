import json
import os
import re
import subprocess
import unicodedata


from gitlab import MAINTAINER_ACCESS, Gitlab


def slugify(value):
    """
    Transofrm text into slug.

    Convert to ASCII.
    Convert spaces to hyphens.
    Remove characters that aren't alphanumerics, underscores, or hyphens.
    Convert to lowercase.
    Also strip leading and trailing whitespace.
    """
    value = str(value)
    value = (
        unicodedata.normalize("NFKD", str(value))
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    value = re.sub(r"[^\w\s-]", "", value.casefold()).strip()
    return re.sub(r"[-\s]+", "-", value)


def get_cookiecutter_conf():
    """Get cookiecutter configuration"""
    with open("cookiecutter.json", "r") as f:
        return json.loads(f.read())


class GitlabSync:
    """A GitLab interface."""

    def __init__(self, *args, **kwargs):
        """Initialize the instance."""
        self.protocol = "https://"
        self.server_url = "gitlab.com"
        self.gl = Gitlab(
            f"{self.protocol}{self.server_url}",
            private_token=os.environ["GITLAB_PRIVATE_TOKEN"],
        )
        self.gl.auth()

    def is_group_slug_available(self, group_slug):
        """Tell if group name is available."""
        for p in self.gl.groups.list(search=group_slug):
            if p.path == group_slug:
                return False
        for u in self.gl.users.list(username=group_slug):
            if (
                u.web_url.replace(f"{self.protocol}{self.server_url}/", "").casefold()
                == group_slug.casefold()
            ):
                return False
        return True

    def create_group(self, project_name, group_slug):
        """Create a GitLab group."""
        self.group = self.gl.groups.create({"name": project_name, "path": group_slug})
        server_link = f"{self.protocol}{self.server_url}"
        group_link = f"{self.protocol}{self.group.path}.{self.server_url}"
        pipeline_badge_link = "/%{project_path}/pipelines"
        pipeline_badge_image_url = (
            "/%{project_path}/badges/%{default_branch}/pipeline.svg"
        )
        self.group.badges.create(
            {
                "link_url": f"{server_link}{pipeline_badge_link}",
                "image_url": f"{server_link}{pipeline_badge_image_url}",
            }
        )
        self.orchestrator = self.gl.projects.create(  # noqa
            {"name": "Orchestrator", "namespace_id": self.group.id}
        )
        self.backend = self.gl.projects.create(  # noqa
            {"name": "Backend", "namespace_id": self.group.id}
        )
        coverage_badge_image_url = (
            "/%{project_path}/badges/%{default_branch}/coverage.svg"
        )
        self.group.badges.create(
            {
                "link_url": f"{group_link}/{self.backend.path}",
                "image_url": f"{server_link}{coverage_badge_image_url}",
            }
        )
        self.frontend = self.gl.projects.create(  # noqa
            {"name": "Frontend", "namespace_id": self.group.id}
        )

    def set_default_branch(self):
        """Set default branch."""
        self.orchestrator.default_branch = "develop"
        self.orchestrator.save()
        self.backend.default_branch = "develop"
        self.backend.save()
        self.frontend.default_branch = "develop"
        self.frontend.save()

    def set_members(self):
        """Add git user or given members to gitlab group."""
        list_members = []
        git_user_email = subprocess.check_output(
            ["git", "config", "user.email"], text=True
        ).split("\n")[0]
        try:
            gitlab_username = self.gl.users.list(search=git_user_email)[0].username
        except IndexError:
            warnings.warn("git local user doesn't exists")
        else:
            list_members.append(gitlab_username)
        members = input(
            "Insert the usernames of all users you want to add to the group, "
            "separated by comma or empty to skip: "
        )
        if members:
            list_members.extend(members.split(","))
        for member in list_members:
            try:
                user = self.gl.users.list(username=member.strip())[0]
            except IndexError:
                print(f"{member} doesn't exists. Please add him from gitlab.com")
            else:
                self.group.members.create(
                    {"user_id": user.id, "access_level": MAINTAINER_ACCESS}
                )
                print(f"{member} added to group {self.group.name}")

    def update_cookiecutter_conf(self):
        """Update cookiecutter configuration file"""
        conf = {}
        with open("cookiecutter.json", "r") as f:
            conf = json.loads(f.read())
        with open("cookiecutter.json", "w+") as f:
            conf["gitlab_group_slug"] = self.group_slug
            f.write(json.dumps(conf, indent=2))

    def git_init(self):
        """Initialize local git repository."""
        os.system(f"./scripts/git_init.sh {self.orchestrator.ssh_url_to_repo}")
        os.system(
            "cd backend && ../scripts/git_init.sh " f"{self.backend.ssh_url_to_repo}"
        )
        os.system(
            "cd frontend && ../scripts/git_init.sh " f"{self.frontend.ssh_url_to_repo}"
        )

    def update_readme(self):
        """Update README.md replacing the Gitlab group placeholder with group slug."""
        placeholder = "__GITLAB_GROUP__"
        filename = "README.md"
        filedata = ""
        with open(filename, "r") as f:
            filedata = f.read()
        filedata = filedata.replace(placeholder, self.group_slug)
        with open(filename, "w+") as f:
            f.write(filedata)

    def run(self):
        """Run the main process operations."""
        cookiecutter_conf = get_cookiecutter_conf()
        default_group_slug = cookiecutter_conf["project_slug"]
        group_slug = (
            input(f"Choose the gitlab group path slug [{default_group_slug}]: ")
            or default_group_slug
        )
        self.group_slug = slugify(group_slug)
        while not self.is_group_slug_available(self.group_slug):
            self.group_slug = input(
                f"A Gitlab group named '{self.group_slug}' already exists. "
                "Please choose a different name and try again: "
            )
        self.create_group(cookiecutter_conf["project_name"], self.group_slug)
        self.update_cookiecutter_conf()
        self.update_readme()
        self.set_members()
        self.git_init()
        self.set_default_branch()


if __name__ == "__main__":
    gl = GitlabSync()
    gl.run()
