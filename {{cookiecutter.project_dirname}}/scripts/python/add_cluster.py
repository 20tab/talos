#!/usr/bin/env python3
"""Define Cluster class and utilities."""

import base64
import json
import sys
from pathlib import Path

from gitlab_sync import GitlabSync
from kubernetes import client, config


def main():
    """Define main function."""
    try:
        cluster_name = json.loads(Path("cookiecutter.json").read_text())["cluster_name"]
    except KeyError:
        sys.exit(
            "'cluster_name' value is missing in 'cookiecutter.json'. "
            "Add it and excute `add_cluster.py` again!"
        )
    # extract certificate
    config.load_kube_config()
    configuration = client.Configuration.get_default_copy()
    certificate = Path(configuration.ssl_ca_cert).read_text()
    # extract token
    v1 = client.CoreV1Api()
    service_accounts = v1.list_namespaced_service_account(
        "kube-system", field_selector="metadata.name=gitlab"
    ).to_dict()
    token_name = service_accounts["items"][0]["secrets"][0]["name"]
    secrets = v1.list_namespaced_secret(
        "kube-system", field_selector=f"metadata.name={token_name}"
    ).to_dict()
    token_str = secrets["items"][0]["data"]["token"]
    token_bytes = base64.b64decode(token_str)
    token = token_bytes.decode()
    # add cluster
    if token:
        gl = GitlabSync()
        group = gl.get_group()
        group.clusters.create(
            {
                "name": cluster_name,
                "platform_kubernetes_attributes": {
                    "api_url": configuration.host,
                    "token": token,
                    "ca_cert": certificate,
                },
                "managed": False,
            }
        )
        print(f"Cluster {cluster_name!r} added to the GitLab group.")
    else:
        print("Token not found. Check if gitlab-admin-service-account.yaml is applied.")


if __name__ == "__main__":
    main()
