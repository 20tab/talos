#!/usr/bin/env python3
"""Define K8s setup."""

import os
import re


def validate_email(email):
    """Define validate email function."""
    if re.match("(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", email) != None:
        return email
    else:
        print(
            "\033[31m" + "Email address is not valid. "
            "Please enter a valid email address." + "\033[37m"
        )
        return input_docker_email(email)


def input_docker_email(email):
    """Define input email with validation function."""
    email = input("Enter DOCKER_EMAIL: ")
    return validate_email(email)


def main():
    """Define main function."""
    DOCKER_REGISTRY_SERVER = input("Enter DOCKER_REGISTRY_SERVER: ")
    DOCKER_USER = input("Enter DOCKER_USER: ")
    DOCKER_PASSWORD = input("Enter DOCKER_PASSWORD: ")
    DOCKER_EMAIL = input_docker_email(None)
    NAMESPACE = input("Enter NAMESPACE: ")

    print(
        f"You are running the following commands:\n"
        "\033[33m" + "\033[1m" + f"kubectl apply -f k8s/development \n"
        f"kubectl create secret docker-registry regcred --docker-server={DOCKER_REGISTRY_SERVER} "
        f"--docker-username={DOCKER_USER} --docker-password={DOCKER_PASSWORD} "
        f"--docker-email={DOCKER_EMAIL} --namespace={NAMESPACE}"
        + "\033[37m"
        + "\033[0m"
    )
    CONFIRM = input("Confirm if you want to continue [Y/n]: ")

    if not CONFIRM or CONFIRM == "Y" or CONFIRM == "y":
        print("Confirmed, K8s setup is running now.")
        os.system(f"kubectl apply -f k8s/development")
        os.system(
            f"kubectl create secret docker-registry regcred --docker-server={DOCKER_REGISTRY_SERVER} "
            f"--docker-username={DOCKER_USER} --docker-password={DOCKER_PASSWORD} "
            f"--docker-email={DOCKER_EMAIL} --namespace={NAMESPACE}"
        )
    else:
        print("K8s setup aborted!")


if __name__ == "__main__":
    main()
