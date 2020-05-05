# 20tab standard project

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)
[![Build Status](https://travis-ci.com/20tab/20tab-standard-project.svg?branch=master)](https://travis-ci.com/20tab/20tab-standard-project?branch=master)

> A [20tab](https://www.20tab.com/) standard project cookiecutter template.

## 📝 Conventions

In the following instructions, replace:

- `projects` with your actual projects directory
- `project_name` with your chosen project name

## 🧩 Requirements

### Cookiecutter

[Cookiecutter](https://cookiecutter.readthedocs.io) must be installed in order to create and initialize the project structure.

```console
$ pip install --user cookiecutter
```

### Kubernetes

Install the `kubectl` command-line tool, if the Kubernetes integration is needed.

- macOS

  ```console
  $ brew install kubectl
  ```

- Linux

  ```console
  $ sudo snap install kubectl --classic
  ```

### GitLab

Install the `python-gitlab` package, if the GitLab integration is needed.

```console
$ pip install --user python-gitlab
```

A GitLab user account is required by the setup procedure to create the repositories, and by Kubernetes to pull the images from the Docker registry.

Put the GitLab Access Token of the chosen user in an environment variable (e.g. export it in the command line or add it to the bash config).

```console
$ export GITLAB_PRIVATE_TOKEN={{gitlab_private_token}}
```

**Note:** the access token can be generated from the GitLab settings "Access Tokens"
section. Make sure to give it full permission. Beware that GitLab only shows the token right after creation, and hides it thereafter.

### DigitalOcean

Install the `doctl` command-line tootl and authenticate, if the DigitalOcean integration is needed.

- macOS

  ```console
  $ brew install doctl
  ```

- Linux

  ```console
  $ snap install doctl
  $ sudo snap connect doctl:kube-config
  ```

Use the `doctl` command-line tool to authenticate.

```console
$ doctl auth init
```

Install the `python-digitalocean` package, if the DigitalOcean integration is needed.

```console
$ pip install --user python-digitalocean
```

A DigitalOcean user account is required by the setup procedure to configure the GitLab integration.

Put the DigitalOcean Access Token of the chosen user in an environment variable (e.g. export it in the command line or add it to the bash config).

**Note:** the access token can be generated from the DigitalOcean settings **"API -> Generate New Token"** section.
Beware that DigitalOcean only shows the token right after creation, and hides it thereafter.

```console
$ export DIGITALOCEAN_ACCESS_TOKEN={{digitalocean_access_token}}
```

## 🚀️ Quickstart

Change directory and create a new project as in this example:

```console
$ cd ~/projects/
$ cookiecutter https://github.com/20tab/20tab-standard-project
You've downloaded /home/paulox/.cookiecutters/20tab-standard-project before. Is it okay to delete and re-download it? [yes]: yes
project_name: My project name
project_slug [myprojectname]:
domain_url [myprojectname.com]:
Select use_gitlab:
1 - Yes
2 - No
Choose from 1, 2 [1]:
Select use_media_volume:
1 - Yes
2 - No
Choose from 1, 2 [1]:
$ cd myprojectname
```

## Setup

### DigitalOcean

1. Select an existing Kubernetes cluster on DigitalOcean or create one with **Create -> Clusters**
2. Run `./scripts/do_setup.sh`

### GitLab

1. Run `./scripts/add_cluster.sh` to connect GitLab with the DigitalOcean hosted Kubernetes cluster

### Kubernetes

1. Change the host to the `ingress.yaml` file and add the domain among the `ALLOWED_HOSTS` in `secrets.yaml`
2. Apply of the `development` directory with `kubectl apply -f k8s/development` (on all three projects the first commit must be done on develop)
3. Run
    ```console
    $ kubectl create secret docker-registry regcred --docker-server=http://registry.gitlab.com --docker-username=gitlab-20tab --docker-password=<PASSWORD> --docker-email=gitlab@20tab.com --namespace=<NAMESPACE>
    ```
4. Git push on frontend and backend (on develop)
