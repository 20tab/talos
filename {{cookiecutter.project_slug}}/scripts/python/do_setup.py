"""Define Digital Ocean setup."""

import json
import os
from pathlib import Path

from kubernetes import Cluster


def get_cluster_name():
    """Get and update cluster name from cookiecutter.json."""
    cookiecutter_path = Path("cookiecutter.json")
    configuration = json.loads(cookiecutter_path.read_text())
    try:
        cluster_name = configuration["cluster_name"]
    except KeyError:
        while not cluster_name:
            cluster_name = input("Please insert the cluster name: ")
    finally:
        configuration["cluster_name"] = cluster_name
        cookiecutter_path.write_text(json.dumps(configuration, indent=2))
    return cluster_name


def main():
    """Define main function."""
    cluster_name = get_cluster_name()
    cluster = Cluster()
    cluster.load_by_name(cluster_name)

    os.system(f"doctl kubernetes cluster kubeconfig save {cluster.name}")
    os.system(f"kubectl config use-context do-{cluster.region}-{cluster.name}")


if __name__ == "__main__":
    main()
