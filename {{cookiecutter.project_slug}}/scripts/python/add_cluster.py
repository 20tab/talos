#!/usr/bin/env python3
"""Define Cluster class and utilities."""

import base64
import json
import os
import sys
from pathlib import Path

from gitlab_sync import GitlabSync
from kubernetes import Cluster


def main():
    """Define main function."""
    try:
        cluster_name = json.loads(Path("cookiecutter.json").read_text())["cluster_name"]
    except KeyError:
        sys.exit(
            "'cluster_name' value is missing in 'cookiecutter.json'. "
            "Add it and excute `add_cluster.py` again!"
        )

    cluster = Cluster()
    cluster.load_by_name(cluster_name)
    credentials = cluster.load_credentials()

    gl = GitlabSync()
    group = gl.get_group()

    certificate_str = credentials["certificate_authority_data"]
    certificate_bytes = base64.b64decode(certificate_str)
    certificate = certificate_bytes.decode()
    token = None
    with open("do_token.yaml") as f:
        for line in f.readlines():
            couple = line.split(":")
            try:
                key = couple[0].strip()
                value = couple[1].strip()
                if key == "token":
                    token = value
            except KeyError:
                continue
            except IndexError:
                continue

    if token:
        cluster = group.clusters.create(
            {
                "name": cluster_name,
                "platform_kubernetes_attributes": {
                    "api_url": credentials["server"],
                    "token": token,
                    "ca_cert": certificate,
                },
                "managed": False,
            }
        )
        os.remove("do_token.yaml")
    else:
        print(
            "Token not found. Please check do_token.yaml file into the projects' root."
        )


if __name__ == "__main__":
    main()
