from gitlab import Gitlab
import os
import sys


class GitlabSync:

    def __init__(self, *args, **kwargs):
        self.gl = Gitlab('https://gitlab.com', private_token=os.environ['GITLAB_PRIVATE_TOKEN'])
        self.gl.auth()

    def is_group_available(self, group_name):
        for p in self.gl.groups.list(search=group_name):
            if p.path == group_name:
                return False
        return True


gls = GitlabSync()
if not gls.is_group_available("{{ cookiecutter.gitlab_group}}"):
    print("Gitlab group already exists! Please choose another group name and try again.")
    sys.exit(1)
    