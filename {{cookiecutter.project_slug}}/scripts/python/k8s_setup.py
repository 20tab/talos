#!/usr/bin/env python3
"""Define K8s setup."""

import re
import subprocess
from getpass import getpass


def validate_email(email):
    """Define validate email function."""
    if (
        re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", email)
        is not None
    ):
        return email
    else:
        raise ValueError


def input_docker_email():
    """Define input email with validation function."""
    email = input("Enter DOCKER_EMAIL: ")
    try:
        return validate_email(email)
    except Exception:
        print(
            "\033[31m" + "Email address is not valid. "
            "Please enter a valid email address." + "\033[37m"
        )
        return input_docker_email()


def main():
    """Define main function."""
    DOCKER_REGISTRY_SERVER = input("Enter DOCKER_REGISTRY_SERVER: ")
    DOCKER_USER = input("Enter DOCKER_USER: ")
    DOCKER_PASSWORD = getpass("Enter DOCKER_PASSWORD: ")
    DOCKER_EMAIL = input_docker_email()
    NAMESPACE = input("Enter NAMESPACE: ")

    print(
        "You are running the following commands:\n"
        "\033[33m" + "\033[1m" + "kubectl create secret docker-registry regcred "
        f"--docker-server={DOCKER_REGISTRY_SERVER} "
        f"--docker-username={DOCKER_USER} --docker-password=_DOCKER_PASSWORD_ "
        f"--docker-email={DOCKER_EMAIL} --namespace={NAMESPACE}"
        + "\033[37m"
        + "\033[0m"
    )
    CONFIRM = input("Confirm if you want to continue [Y/n]: ")

    if not CONFIRM or CONFIRM == "Y" or CONFIRM == "y":
        print("Confirmed, K8s setup is running now.")
        subprocess.run(
            [
                "kubectl",
                "create",
                "secret",
                "docker-registry",
                "regcred",
                f"--docker-server={DOCKER_REGISTRY_SERVER}",
                f"--docker-username={DOCKER_USER}",
                f"--docker-password={DOCKER_PASSWORD}",
                f"--docker-email={DOCKER_EMAIL}",
                f"--namespace={NAMESPACE}",
            ]
        )
    else:
        print("K8s setup aborted!")


if __name__ == "__main__":
    main()
