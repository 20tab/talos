"""Define Cluster class and utilities."""

import base64

from gitlab_sync import GitlabSync
from kubernetes import Cluster
from utils import get_cookiecutter_conf


def main():
    """Define main function."""
    try:
        cluster_name = get_cookiecutter_conf()["cluster_name"]
    except KeyError:
        cluster_name = input("Please insert the cluster name: ")
        while not cluster_name:
            cluster_name = input("Please insert the cluster name: ")

    cluster = Cluster()
    cluster.load_by_name(cluster_name)
    credentials = cluster.load_credentials()

    gl = GitlabSync()
    group = gl.get_group()

    certificate_str = credentials["certificate_authority_data"]
    certificate_bytes = base64.b64decode(certificate_str)
    certificate = certificate_bytes.decode()

    cluster = group.clusters.create(
        {
            "name": cluster_name,
            "platform_kubernetes_attributes": {
                "api_url": credentials["server"],
                "token": credentials["token"],
                "ca_cert": certificate,
            },
            "managed": False,
        }
    )


if __name__ == "__main__":
    main()
