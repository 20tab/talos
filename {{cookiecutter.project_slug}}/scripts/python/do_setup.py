import os

from kubernetes import Cluster
from utils import get_cluster_name


def main():
    """Define main function."""
    cluster_name = get_cluster_name()
    cluster = Cluster()
    cluster.load_by_name(cluster_name)

    os.system(f"doctl kubernetes cluster kubeconfig save {cluster.name}")
    os.system(f"kubectl config use-context do-{cluster.region}-{cluster.name}")


if __name__ == "__main__":
    main()
