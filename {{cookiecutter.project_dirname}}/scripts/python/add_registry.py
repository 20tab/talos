#!/usr/bin/env python3
"""Add gitlab registry authorization to K8s cluster."""

import base64
import json

from gitlab_sync import GitlabSync
from kubernetes import client, config


def main():
    """Define main function."""
    gl = GitlabSync()
    group = gl.get_group()
    token = group.deploytokens.create(
        {
            "name": "k8s registry",
            "scopes": ["read_registry"],
            "username": "",
            "expires_at": "",
        }
    )
    config.load_kube_config()
    v1 = client.CoreV1Api()
    cred_payload = {
        "auths": {
            "registry.gitlab.com": {
                "username": token.username,
                "password": token.token,
            }
        }
    }
    data = {
        ".dockerconfigjson": base64.b64encode(
            json.dumps(cred_payload).encode()
        ).decode()
    }
    secret = client.V1Secret(
        api_version="v1",
        data=data,
        kind="Secret",
        metadata=dict(
            name="regcred", namespace="{{ cookiecutter.project_slug }}-development"
        ),
        type="kubernetes.io/dockerconfigjson",
    )
    v1.create_namespaced_secret(
        "{{ cookiecutter.project_slug }}-development", body=secret
    )
    print("K8s setup complete!")


if __name__ == "__main__":
    main()
