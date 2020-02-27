"""Tests cookiecutter project generation."""

import json
import os
import re

import pytest
from binaryornot.check import is_binary

PATTERNS = {
    "cookiecutter": r"{{(\s?cookiecutter)[.](.*?)}}",
    "environment": r"__ENVIRONMENT__",
    "configuration": r"__CONFIGURATION__",
    "gitlab_group": r"__GITLAB_GROUP__",
}


@pytest.fixture
def context():
    """It's a context not using gitlab."""
    return {
        "project_name": "MyTestProject",
        "project_slug": "mytestproject",
        "use_gitlab": "No",
    }


def build_files_list(root_dir):
    """Build a list containing absolute paths to the generated files."""
    return [
        os.path.join(dirpath, file_path)
        for dirpath, subdirs, files in os.walk(root_dir)
        for file_path in files
    ]


def check_paths(paths):
    """Check all paths have correct substitutions."""
    for path in paths:
        if is_binary(path) or path.endswith(".tpl") or path.endswith(".py"):
            continue

        for line in open(path, "r"):
            for k, pattern in PATTERNS.items():
                re_obj = re.compile(pattern)
                match = re_obj.search(line)
                msg = f"{k} variable not replaced in {path}"
                assert match is None, msg


def get_cookicutter_conf(project_path):
    """Retrieve cookiecutter.json file."""
    path = f"{project_path}/cookiecutter.json"
    assert os.path.exists(path)
    with open(path, "r") as f:
        return json.loads(f.read())


def test_project_generation(cookies, context):
    """Test that project is generated and fully rendered."""
    result = cookies.bake(extra_context={**context})
    assert result.exit_code == 0
    assert result.exception is None
    assert result.project.basename == context["project_slug"]
    assert result.project.isdir()
    project_dir_path = str(result.project)
    cookicutter_conf = get_cookicutter_conf(project_dir_path)
    assert "gitlab_group_slug" in cookicutter_conf.keys()
    assert cookicutter_conf["gitlab_group_slug"] is None
    assert "project_slug" in cookicutter_conf.keys()

    paths = build_files_list(str(result.project))
    assert paths
    check_paths(paths)
