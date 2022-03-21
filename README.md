
# Talos

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)

> A [20tab](https://www.20tab.com/) standard project.

## 🧩 Requirements

The Talos script can be run either using Docker or as a local shell command.

### 🐋 Docker

In order to run Talos via Docker, a working [Docker installation](https://docs.docker.com/get-docker/) is the only requirement.

### 👨‍💻 Shell command

In order to run Talos as a shell command, first clone the repository in a local projects directory
```console
cd ~/projects
git clone https://github.com/20tab/20tab-standard-project.git talos
```
Then, install the following requirements
| Requirements | Instructions |
|--|--|
|🌎 Terraform  | [Install Guide](https://learn.hashicorp.com/tutorials/terraform/install-cli)  |
|🐍 Python Dependencies | `pip install -r talos/requirements/common.txt` |

## 🔑 Credentials

### 🌊 DigitalOcean
If DigitalOcean is chosen for deployment, a Personal Access Token with _write_ permission is required.
Additionally if DigitalOcean Spaces is the chosen media storage backend, a pair of S3 access keys is required.

**Note:** all credentials can be generated in the DigitalOcean API configuration section.
⚠️ Beware that the token is shown only once after creation.

### 🦊 GitLab
If the GitLab integration is enabled, a Personal Access Token with _api_ permission is required.
It can be generated in the GitLab User Settings panel.

**Note:** the token can be generated in the Access Tokens section of the GitLab User Settings panel.
⚠️ Beware that the token is shown only once after creation.

## 🚀️ Quickstart

Change to the projects directory, for example
```console
cd ~/projects
```

### 🐋 Docker

```console
docker run --interactive --tty --rm --volume $PWD:/data 20tab/talos:latest
```

### 👨‍💻 Shell command

```console
./talos/setup.py
```

# TODO: update example

```console

```
