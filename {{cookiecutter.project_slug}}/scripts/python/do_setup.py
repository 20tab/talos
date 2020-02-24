import os

from kubernetes import Cluster
from utils import get_cookiecutter_conf, update_cookiecutter_conf


def main():
    """Define main function."""
    try:
        cluster_name = get_cookiecutter_conf()["cluster_name"]
    except KeyError:

        cluster_name = input("Please insert the cluster name: ")
        while not cluster_name:
            cluster_name = input("Please insert the cluster name: ")
        update_cookiecutter_conf("cluster_name", cluster_name)

    cluster = Cluster()
    cluster.load_by_name(cluster_name)

    os.system(f"doctl kubernetes cluster kubeconfig save {cluster.name}")
    os.system(f"kubectl config use-context do-{cluster.region}-{cluster.name}")


if __name__ == "__main__":
    main()
