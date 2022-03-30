# {{ cookiecutter.project_name }} <!-- omit in toc -->

This is the "{{ cookiecutter.project_name }}" orchestrator.

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

The first run is manual, made from [GitLab Pipeline](https://gitlab.com/{{ cookiecutter.project_slug }}/orchestrator/-/pipelines/new).

To create all the terraform resources, run the pipeline with the following variable:

`ENABLED_ALL`= `true`

If you want to choose what to activate to limit any costs, read below.

### Stages

{% if cookiecutter.deployment_type == "digitalocean-k8s" %}Core stage will create Kubernetes Cluster{% if cookiecutter.media_storage == "digitalocean-s3" %}, S3 Spaces{% endif %} and Databases Cluster.
{% endif %}Networking stage will create Ingress, Certificate and Monitoring if enabled.
Environment stage will create the other resource for each of it.

Value  | Description
------------- | -------------
{% if cookiecutter.deployment_type == "digitalocean-k8s" %}C`core` | Core stage will create Kubernetes Cluster{% if cookiecutter.media_storage == "digitalocean-s3" %}, S3 Spaces{% endif %} and Databases Cluster
{% endif %}`networking` | Networking stage will create Ingress, Certificate and Monitoring if enabled.
`environment`  | Environment stage will create the other resource for each of it.

`ENABLED_STAGE` = `{% if cookiecutter.deployment_type == "digitalocean-k8s" %}core{% endif %}, networking, environment`

### Stacks

{% if cookiecutter.environment_distribution == "1" %}You have opted to have all environments share the same stack.

`ENABLED_STACKS` = `main`{% endif %}{% if cookiecutter.environment_distribution == "2" %}You have opted to have Dev and Stage environments share the same stack, Prod has its own.

`ENABLED_STACKS` = `dev, main`{% endif %}{% if cookiecutter.environment_distribution == "3" %}Each environment has its own stack

`ENABLED_STACKS` = `main, dev, prod`{% endif %}

### Environments

Value  | Description
------------- | -------------
`dev` | Development is the first delivery environment for developers.
`stage` | Staging is the test environment for customers.
`prod`  | Production is the public production environment accessible to all users.

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

Clone the orchestrator and services repositories:

```console
git clone git@gitlab.com:{{ cookiecutter.project_slug }}/orchestrator.git {{ cookiecutter.project_dirname }}
cd {{ cookiecutter.project_dirname }}{% if cookiecutter.backend_type != 'none' %}
git clone -b develop git@gitlab.com:{{ cookiecutter.project_slug }}/{{ cookiecutter.backend_service_slug }}.git{% endif %}{% if cookiecutter.frontend_type != 'none' %}
git clone -b develop git@gitlab.com:{{ cookiecutter.project_slug }}/{{ cookiecutter.frontend_service_slug }}.git{% endif %}
cd ..
```

**NOTE** : We're cloning the `develop` branch for all repo.

### Environment variables

In order for the project to run correctly, a number of environment variables must be set in an `.env` file inside the orchestrator directory. For ease of use, a `.env_template` template is provided.

Enter the newly created **project** directory and create the `.env` file copying from `.env_template`:

```console
$ cd ~/projects/{{ cookiecutter.project_dirname }}
$ cp .env_template .env
```

### Docker

All the following Docker commands are supposed to be run from the orchestrator directory.

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

### Create and activate a local SSL Certificate <sup id="a-setup-https-locally">[1](#f-setup-https-locally)</sup>

Move to the `nginx` directory:

```console
$ cd nginx
```

Install the certificate utils:

-   Linux

    ```console
    $ sudo apt-get install openssl libnss3-tools
    ```

-   macOs
    ```console
    $ brew install openssl nss
    ```
    **NOTE** : Follow all steps at the end of the installation (can be displayed again via `brew info <package-name>`).

Create the certificate files:

```console
$ openssl req -config localhost.conf -new -x509 -sha256 -newkey rsa:2048 -nodes -keyout localhost.key -days 1024 -out localhost.crt
```

```console
$ openssl pkcs12 -export -out localhost.pfx -inkey localhost.key -in localhost.crt
```

Import certificate into shared database (password: `localhost`):

```console
$ pk12util -d sql:$HOME/.pki/nssdb -i localhost.pfx
```

**NOTE**: In the event of a `PR_FILE_NOT_FOUND_ERROR` or `SEC_ERROR_BAD_DATABASE` error, run the following commands and try again:

```console
$ mkdir -p $HOME/.pki/nssdb
$ certutil -d $HOME/.pki/nssdb -N
```

Trust the self-signed server certificate:

-   Linux

    ```console
    $ certutil -d sql:$HOME/.pki/nssdb -A -t "P,," -n 'dev cert' -i localhost.crt
    ```

-   macOS
    ```console
    $ sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain localhost.crt
    ```

<a id="f-setup-https-locally" href="#a-setup-https-locally">1</a>. For further reference look [here](https://medium.com/@workockmoses/how-to-setup-https-for-local-development-on-ubuntu-with-self-signed-certificate-f97834064fd).
