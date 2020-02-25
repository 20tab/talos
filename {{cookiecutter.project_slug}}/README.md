# {{cookiecutter.project_name}} <!-- omit in toc -->

This is the "{{cookiecutter.project_name}}" orchestrator.

## Index <!-- omit in toc -->

- [Quickstart](#quickstart)
  - [Git](#git)
    - [Clone](#clone)
  - [Environment variables](#environment-variables)
  - [Docker](#docker)
    - [Build](#build)
    - [Run](#run)
  - [Makefile shortcuts](#makefile-shortcuts)
    - [Pull](#pull)
    - [Django manage command](#django-manage-command)
    - [Restart and build services](#restart-and-build-services)
  - [Create SSL Certificate <sup id="a-setup-https-locally">1</sup>](#create-ssl-certificate-sup-ida-setup-https-locally1sup)
  - [Create and activate a local SSL Certificate <sup id="a-setup-https-locally">1</sup>](#create-and-activate-a-local-ssl-certificate-sup-ida-setup-https-locally1sup)
    - [Install the cert utils](#install-the-cert-utils)
      - [Ubuntu](#ubuntu)
      - [Mac Os](#mac-os)
    - [Import certificates](#import-certificates)
    - [Trust the self-signed server certificate](#trust-the-self-signed-server-certificate)
      - [Ubuntu](#ubuntu-1)
      - [Mac Os](#mac-os-1)
- [Useful commands](#useful-commands)

## Quickstart

This section explains the steps you need to clone and work wityh this project.

1. [clone](#clone) the project code
2. set all the required [environment variables](#environment-variables)
3. [build](#build) all the services
4. [create a superuser](#create-a-superuser) to login the platform
5. [run](#run) all the services
6. login using the URL: http://localhost:8080

### Git

#### Clone

Clone the repositories of the orchestrator, backend and frontend:

```shell
$ git clone -b develop git@gitlab.com:__GITLAB_GROUP__/orchestrator.git {{cookiecutter.project_slug}} && cd {{cookiecutter.project_slug}}
$ git clone -b develop git@gitlab.com:__GITLAB_GROUP__/backend.git
$ git clone -b develop git@gitlab.com:__GITLAB_GROUP__/frontend.git
```
**NOTE** : We're cloning the `develop` branch for all repo.

### Environment variables

In order for the project to run correctly, a number of environment variables must be set in an `.env` file inside the orchestrator directory. For ease of use, a `.env.tpl` template is provided.

Enter the newly created **project** directory and crate the `.env` file coopying from ``.env.tpl`:

```shell
$ cd ~/projects/{{cookiecutter.project_slug}}
$ cp .env.tpl .env
```

### Docker

All the following Docker commands are supposed to be run from the orchestrator directory.

#### Build

```shell
$ docker-compose build
```

#### Run

```shell
$ docker-compose up
```
**NOTE**: It can be daemonized adding the `-d` flag.

### Makefile shortcuts

#### Pull

Pull the main git repo and the sub-repos:

```shell
$ make pull
```

#### Django manage command

Use the Django `manage.py` command shell:

```shell
$ make django
```

You can pass the specific command:

```shell
$ make django p=check
```

You can pass the container name:

```shell
$ make django p=shell c=backend_2
```

#### Restart and build services

Restart and build all services:

```shell
$ make rebuild
```

You can pass the service name:

```shell
$ make rebuild s=backend
```

### Create SSL Certificate <sup id="a-setup-https-locally">[1](#f-setup-https-locally)</sup>

Move to the `nginx` directory:
```shell
$ cd nginx
```

Create the certificate related files:
```shell
$ openssl req -config localhost.conf -new -x509 -sha256 -newkey rsa:2048 -nodes -keyout localhost.key -days 1024 -out localhost.crt
```

```shell
$ openssl pkcs12 -export -out localhost.pfx -inkey localhost.key -in localhost.crt
```

### Create and activate a local SSL Certificate <sup id="a-setup-https-locally">[1](#f-setup-https-locally)</sup>

#### Install the cert utils

##### Ubuntu
```shell
$ sudo apt-get install libnss3-tools
```

##### Mac Os
```shell
$ brew install nss
```

#### Import certificates

Move to the `nginx` directory
```shell
$ cd nginx
```

Import certificate into shared database (password: `localhost`):
```shell
$ pk12util -d sql:$HOME/.pki/nssdb -i localhost.pfx
```

**NOTE**: In the event of a `PR_FILE_NOT_FOUND_ERROR` or `SEC_ERROR_BAD_DATABASE` error, run the following commands and try again:
```shell
$ mkdir -p $HOME/.pki/nssdb
$ certutil -d $HOME/.pki/nssdb -N
```

#### Trust the self-signed server certificate

##### Ubuntu
```shell
$ certutil -d sql:$HOME/.pki/nssdb -A -t "P,," -n 'dev cert' -i localhost.crt
```

##### Mac Os
```shell
$ sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain localhost.crt
```

<a id="f-setup-https-locally" href="#a-setup-https-locally">1</a>. For further reference look [here](https://medium.com/@workockmoses/how-to-setup-https-for-local-development-on-ubuntu-with-self-signed-certificate-f97834064fd).

## Useful commands

Useful commands to use after startup:

```
$ kubectl get deployments
$ kubectl delete deployment <deployment-name>
$ kubectl scale deployment <deployment-name> --replicas=0
$ kubectl scale deployment <deployment-name> --replicas=1
$ kubectl get pods
# check for k8s errors
$ kubectl describe pod <pod-name>
# check for service errors
$ kubectl logs -f <pod-name>
# run commands on the pod
$ kubectl exec -it <pod-name> bash
```
