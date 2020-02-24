# 20tab standard project <!-- omit in toc -->

A [20tab](https://www.20tab.com/) standard project [cookiecutter](https://github.com/cookiecutter/cookiecutter) template.

## Index <!-- omit in toc -->

- [Conventions](#conventions)
- [Requirements](#requirements)
  - [Cookiecutter](#cookiecutter)
  - [Kubernetes](#kubernetes)
  - [GitLab](#gitlab)
  - [DigitalOcean](#digitalocean)
- [Quickstart](#quickstart)
- [Work in progress](#work-in-progress)
  - [DigitalOcean setup](#digitalocean-setup)
  - [Kubernetes and GitLab connection](#kubernetes-and-gitlab-connection)
  - [Kubernetes apply](#kubernetes-apply)

## Conventions

In the following instructions, replace:

- `projects` with your actual projects directory
- `project_name` with your chosen project name

## Requirements

### Cookiecutter

[Cookiecutter](https://cookiecutter.readthedocs.io) must be installed in order to create and initialize the project structure.

```shell
$ pip install --user cookiecutter
```

### Kubernetes

Install the `kubectl` command-line tool, if the Kubernetes integration is needed.

- macOS

  ```shell
  $ brew install kubectl
  ```

- Linux

  ```shell
  $ sudo snap install kubectl --classic
  ```

### GitLab

Install the `python-gitlab` package, if the GitLab integration is needed.

```shell
$ pip install --user python-gitlab
```

A GitLab user account is required by the setup procedure to create the repositories, and by Kubernetes to pull the images from the Docker registry.

Put the GitLab Access Token of the chosen user in an environment variable (e.g. export it in the command line or add it to the bash config).

```shell
$ export GITLAB_PRIVATE_TOKEN={{gitlab_private_token}}
```

**Note:** the access token can be generated from the GitLab settings "Access Tokens"
section. Make sure to give it full permission. Beware that GitLab only shows the token right after creation, and hides it thereafter.

### DigitalOcean

Install the `doctl` command-line tootl and authenticate, if the DigitalOcean integration is needed.

- macOS

  ```shell
  $ brew install doctl
  ```

- Linux

  ```shell
  $ snap install doctl
  $ sudo snap connect doctl:kube-config
  ```

Put the DigitalOcean Access Token of the chosen user in an environment variable (e.g. export it in the command line or add it to the bash config).

```shell
$ export DIGITALOCEAN_ASCESS_TOKEN={{digitalocean_access_token}}
```

Use the `doctl` command-line tool to authenticate.

```shell
$ doctl auth init
```

Install the `python-digitalocean` package, if the DigitalOcean integration is needed.

```shell
$ pip install --user python-digitalocean
```

## Quickstart

Change directory and create a new project as in this example:

```shell
$ cd ~/projects/
$ cookiecutter https://github.com/20tab/20tab-standard-project
project_name: My project name
project_slug [myprojectname]:
use_gitlab [y]:
Choose the gitlab group path slug [myprojectname]:
Insert the usernames of all users you want to add to the group, separated by comma or empty to skip :
$ cd myprojectname
```

---

## Work in progress

### DigitalOcean setup

- Create a Kubernetes cluster on DigitalOcean **Create -> Clusters**
- Create a token in the **API -> Generate New Token** section or select an existing one
- Run ./scripts/do_setup.sh -c <cluster_name> -r <region>

### Kubernetes and GitLab connection

- Run ./scripts/add_cluster.sh

### Kubernetes apply

- Run `kubectl create secret docker-registry regcred --docker-server=http://registry.gitlab.com --docker-username=gitlab-20tab --docker-password=<PASSWORD> --docker-email=gitlab@20tab.com --namespace=<NAMESPACE>`
- Modificare l'host sul file `ingress.yaml` e aggiungere il dominio tra gli allowed_hosts in `secrets.yaml`
- Apply della cartella `kubectl apply -f k8s/development` (su tutti e tre i progetti il primo commit si deve fare su develop)
- Git push su frontend e backend (su develop)
