# {{ cookiecutter.project_name }} <!-- omit in toc -->

This is the "{{ cookiecutter.project_name }}" {{ cookiecutter.service_slug }}.

## Index <!-- omit in toc -->

-   [Provisioning](#provisioning)
    -   [Stages](#stages)
    -   [Stacks](#stacks)
    -   [Environments](#stage)
-   [Quickstart](#quickstart)
    -   [Git](#git)
        -   [Clone](#clone)
    -   [Environment variables](#environment-variables)
    -   [Docker](#docker)
        -   [Build](#build)
        -   [Run](#run)
    -   [Makefile shortcuts](#makefile-shortcuts)
        -   [Pull](#pull)
        -   [Django manage command](#django-manage-command)
        -   [Restart and build services](#restart-and-build-services)
    -   [Create SSL Certificate <sup id="a-setup-https-locally">1</sup>](#create-ssl-certificate-sup-ida-setup-https-locally1sup)
    -   [Create and activate a local SSL Certificate <sup id="a-setup-https-locally">1</sup>](#create-and-activate-a-local-ssl-certificate-sup-ida-setup-https-locally1sup)
        -   [Install the cert utils](#install-the-cert-utils)
        -   [Import certificates](#import-certificates)
        -   [Trust the self-signed server certificate](#trust-the-self-signed-server-certificate)

## Provisioning

The first run is manual, made from [GitLab Pipeline](https://gitlab.com/{{ cookiecutter.project_slug }}/{{ cookiecutter.service_slug }}/-/pipelines/new).

To create all the terraform resources, run the pipeline with the following variable:

`ENABLED_ALL`= `true`

If you want to choose what to activate to limit any costs, read below.

### Stages

{% if cookiecutter.deployment_type == "digitalocean-k8s" %}Base stage will create Kubernetes Cluster{% if cookiecutter.media_storage == "digitalocean-s3" %}, S3 Spaces{% endif %} and Databases Cluster.
{% endif %}Cluster stage will create Ingress, Certificate and Monitoring if enabled.
Environment stage will create the other resource for each of it.

| Value                                                              | Description                                                                                                                                   |
| ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| {% if cookiecutter.deployment_type == "digitalocean-k8s" %}`base` | Base stage will create Kubernetes Cluster{% if cookiecutter.media_storage == "digitalocean-s3" %}, S3 Spaces{% endif %} and Databases Cluster |
| {% endif %}`cluster`                                               | Cluster stage will create Ingress, Certificate and Monitoring if enabled.                                                                     |
| `environment`                                                      | Environment stage will create the other resource for each of it.                                                                              |

`ENABLED_STAGES` = `{% if cookiecutter.deployment_type == "digitalocean-k8s" %}base, {% endif %}cluster, environment`

### Stacks

{% if cookiecutter.environments_distribution == "1" %}You have opted to have all environments share the same stack.

`ENABLED_STACKS` = `main`{% endif %}{% if cookiecutter.environments_distribution == "2" %}You have opted to have Dev and Stage environments share the same stack, Prod has its own.

`ENABLED_STACKS` = `dev, main`{% endif %}{% if cookiecutter.environments_distribution == "3" %}Each environment has its own stack

`ENABLED_STACKS` = `main, dev, prod`{% endif %}

### Environments

| Value   | Description                                                              |
| ------- | ------------------------------------------------------------------------ |
| `dev`   | Development is the first delivery environment for developers.            |
| `stage` | Staging is the test environment for customers.                           |
| `prod`  | Production is the public production environment accessible to all users. |

`ENABLED_ENVS` = `dev, stage, prod`

## Quickstart

This section explains the steps you need to clone and work with this project.

1. [clone](#clone) the project code
2. set all the required [environment variables](#environment-variables)
3. [build](#build) all the services
4. [create a superuser](#create-a-superuser) to login the platform
5. [run](#run) all the services
6. login using the URL: http://localhost:8080

### Git

#### Clone

Clone the {{ cookiecutter.service_slug }} and services repositories:

```console
git clone __VCS_BASE_SSH_URL__/{{ cookiecutter.service_slug }}.git {{ cookiecutter.project_dirname }}
cd {{ cookiecutter.project_dirname }}{% if cookiecutter.backend_type != 'none' %}
git clone -b develop __VCS_BASE_SSH_URL__/{{ cookiecutter.backend_service_slug }}.git{% endif %}{% if cookiecutter.frontend_type != 'none' %}
git clone -b develop __VCS_BASE_SSH_URL__/{{ cookiecutter.frontend_service_slug }}.git{% endif %}
cd ..
```

**NOTE** : We're cloning the `develop` branch for all repo.

### Environment variables

In order for the project to run correctly, a number of environment variables must be set in an `.env` file inside the {{ cookiecutter.service_slug }} directory. For ease of use, a `.env_template` template is provided.

Enter the newly created **project** directory and create the `.env` file copying from `.env_template`:

```console
$ cd ~/projects/{{ cookiecutter.project_dirname }}
$ cp .env_template .env
```

### Docker

All the following Docker commands are supposed to be run from the {{ cookiecutter.service_slug }} directory.

#### Build

```console
$ docker-compose build
```

#### Run

```console
$ docker-compose up
```

**NOTE**: It can be daemonized adding the `-d` flag.

### Makefile shortcuts

#### Self documentation of Makefile commands

To show the Makefile self documentation help:

```console
$ make
```

#### Pull

Pull the main git repo and the sub-repos:

```console
$ make pull
```

#### Django manage command

Use the Django `manage.py` command shell:

```console
$ make django
```

You can pass the specific command:

```console
$ make django p=check
```

You can pass the container name:

```console
$ make django p=shell c=backend_2
```

#### Restart and build services

Restart and build all services:

```console
$ make rebuild
```

You can pass the service name:

```console
$ make rebuild s=backend
```

### Activate a valid local SSL Certificate

Import the `traefik/20tab.crt` file in your browser to have a trusted ssl certificate:

#### Firefox

-   Settings > Privacy & Security > Manage Certificates > View Certificates... > Authorities > Import

#### Chrome

-   Settings > Security > Certificates > Authorities > Import
