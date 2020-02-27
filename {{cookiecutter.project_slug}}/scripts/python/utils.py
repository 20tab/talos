"""Define utilities."""

import json


def update_cookiecutter_conf(key, value):
    """Update cookiecutter configuration file."""
    conf = {}
    with open("cookiecutter.json", "r") as f:
        conf = json.loads(f.read())
    with open("cookiecutter.json", "w+") as f:
        conf[key] = value
        f.write(json.dumps(conf, indent=2))


def get_cookiecutter_conf():
    """Get cookiecutter configuration."""
    with open("cookiecutter.json", "r") as f:
        return json.loads(f.read())


def get_cluster_name():
    """Get and update cluster name from cookiecutter.json."""
    cluster_name = ""
    try:
        cluster_name = get_cookiecutter_conf()["cluster_name"]
    except KeyError:
        while not cluster_name:
            cluster_name = input("Please insert the cluster name: ")
    finally:
        update_cookiecutter_conf("cluster_name", cluster_name)
    return cluster_name
