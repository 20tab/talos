# 20tab standard project

This is the [20tab](https://www.20tab.com/) standard project [cookiecutter](https://github.com/cookiecutter/cookiecutter) template.

## Outline

* [Conventions](#conventions)
* [Workspace initialization](#workspace-initialization)
    * [Basic requirements](#basic-requirements)
* [Setup a new project](#setup-a-new-project)
    * [Start Project](#start-project)

## Conventions

In the following instructions:
- replace `projects` with your actual projects directory
- replace `project_name` with your chosen project name

## Workspace initialization

### Basic requirements

**Cookiecutter** must be installed before initializing the project.

```shell
$ pip install --user cookiecutter python-gitlab
```

#### Digital Ocean

##### OSX

```shell
$ brew install doctl
```

##### Linux

```shell
$ snap install doctl
$ sudo snap connect doctl:kube-config
```

#### Kubernetes

##### OSX

```shell
$ brew install kubectl
```

##### Linux

```shell
$ sudo snap install kubectl --classic
```

#### GitLab

Make sure a GitLab user exists that will be the repository owner and the one Kubernetes
uses during the deploy procedures.

Put the GitLab Access Token of the chosen user in an env variable before running any
other command. You can export it in the command line or put it in your bash config.

```shell
$ export GITLAB_PRIVATE_TOKEN={{gitlab_private_token}}
```

Note: the access token can be generated from the GitLab settings "Access Tokens"
section. Make sure to give it full permission. Beware that the token is shown and can
be copied only right after creation and it is hidden thereafter.


## New project

This section shows how to create and initialize a project.

### Creation

Change directory and start a project with this template:

```shell
$ cd ~/projects/
$ cookiecutter https://github.com/20tab/20tab-standard-project
project_name [20tab standard project]: project_name
project_slug [project_name]:
use_gitlab [y]:
Choose the gitlab group name [project_name]:
Insert the usernames of all users you want to add to the group, separated by comma:
$ cd project_name
```

Note: in order to make the subsequent commands work, make sure to add at least the
username of the local user to the members list.

---

# WIP

### DigitalOcean setup

- Create a Kubernetes cluster on DigitalOcean **Create -> Clusters**
- Create a token in the **API -> Generate New Token** section or select an existing one
- Login using `doctl auth init` and the selected token
- Salvare la configurazione di kubernetes lanciando `doctl kubernetes cluster kubeconfig save <cluster_name>`
- Settare il context (opzionale, lo fa lui di default) `kubectl config use-context <cluster_name>`
- Installare [ingress-nginx](https://kubernetes.github.io/ingress-nginx/deploy/#docker-for-mac):
    - `kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/nginx-0.28.0/deploy/static/mandatory.yaml`
    - `kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/nginx-0.28.0/deploy/static/provider/cloud-generic.yaml`
- Installare secret per il registro di docker-gitlab:
    - `kubectl create secret docker-registry regcred --docker-server=http://registry.gitlab.com --docker-username=gitlab-20tab --docker-password=<PASSWORD> --docker-email=gitlab@20tab.com`

### Connessione tra kubernetes e gitlab

- Visitare la sezione kubernetes del gruppo.
- Aggiungere il nome del cluster (mettici il cavolo che ti pare)
- Aggiungere **API_URL**: `kubectl cluster-info | grep 'Kubernetes master' | awk '/http/ {print $NF}'`
- Aggiungere Certificato:
  - Lista dei secrets: `kubectl get secrets | grep 'default-token' | awk '{print $1}'` (dovrebbe essere simile a `default-token-xxxxx`)
  - Mostra il certificato: `kubectl get secret default-token-xxxxx -o jsonpath="{['data']['ca\.crt']}" | base64 --decode`
  - Incollare il certificato su gitlab
- Aggiungere token:
  - Eseguire l'apply del file `kubectl apply -f k8s/gitlab-admin-service-account.yaml`
  - Stampa il token per il servizio creato: `kubectl -n kube-system describe secret $(kubectl -n kube-system get secret | grep gitlab-admin | awk '{print $1}')`
  - Copiare <authentication_token> dall'output:
  ```shell
    Name:         gitlab-admin-token-b5zv4
    Namespace:    kube-system
    Labels:       <none>
    Annotations:  kubernetes.io/service-account.name=gitlab-admin
                kubernetes.io/service-account.uid=bcfe66ac-39be-11e8-97e8-026dce96b6e8

    Type:  kubernetes.io/service-account-token

    Data
    ====
    ca.crt:     1025 bytes
    namespace:  11 bytes
    token:      <authentication_token>
  ```
- Assicurarsi di rimuovere la spunta da gitlab-managed cluster
- Salvare le impostazioni su gitlab

### Apply dell'orchestratore

- Modificare l'host sul file `ingress.yaml` e aggiungere il dominio tra gli allowed_hosts in `secrets.yaml`
- Apply della cartella `kubectl apply -f k8s/development` (su tutti e tre i progetti il primo commit si deve fare su develop)
- Git push su frontend e backend (su develop)

#### FIXME
```
Error from server (Invalid): error when creating "k8s/development/ingress.yaml": Ingress.extensions "development-rocchettacontest2020-ingress-service" is invalid: spec.rules[0].http.backend.serviceName: Invalid value: "development-rocchettacontest2020-static-nginx-cluster-ip-service": must be no more than 63 characters
Error from server (Invalid): error when creating "k8s/development/staticfiles.yaml": Service "development-rocchettacontest2020-static-nginx-cluster-ip-service" is invalid: metadata.name: Invalid value: "development-rocchettacontest2020-static-nginx-cluster-ip-service": must be no more than 63 characters
```

## Existing project

1. [clone](#clone) the project code
2. set all the [environment variables](#environment-variables)
3. [build](#build) all the services
4. [create a superuser](#create-a-superuser) to login the platform
5. [run](#run) all the services
6. login using the URL: http://localhost:8080

## Git

### Clone

Clone the main repo and fetch the sub-repos in such a way to have the `.git` folder
inside the sub-dirs:
```shell
$ git clone git@gitlab.com:__GITLAB_GROUP__/orchestrator.git {{cookiecutter.project_slug}} && cd {{cookiecutter.project_slug}}
$ git clone git@gitlab.com:__GITLAB_GROUP__/backend.git
$ git clone git@gitlab.com:__GITLAB_GROUP__/frontend.git
```

## Environment variables

In order for the project to run correctly, a number of environment variables must be set in an `.env` file inside the orchestrator directory. For ease of use, a `.env.tpl` template is provided for each of the aforementioned files.

## Docker

All the following Docker commands are supposed to be run from the orchestrator directory.

### Build

```shell
$ docker-compose build
```

### Run

```shell
$ docker-compose up
```
**NOTE**: It can be daemonized adding the `-d` flag.

## Makefile shortcuts

### Pull

Pull the main git repo and the sub-repos:

```shell
$ make pull
```

### Django manage command

Use the Django `manage.py` command shell:

```shell
$ make django
```

You can pass the specific command:

```shell
$ make django p=check
```

### Create a superuser

Create a Django superuser to log in the admin:

```shell
$ make createsuperuser
```

You can pass the container name:

```shell
$ make createsuperuser c=portaleformazione_backend_2
```

### Restart and build services

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

Install the cert utils:

#### Ubuntu
```shell
$ sudo apt-get install libnss3-tools
```

#### Mac Os
```shell
$ brew install nss
```

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

Trust the self-signed server certificate:

#### Ubuntu
```shell
$ certutil -d sql:$HOME/.pki/nssdb -A -t "P,," -n 'dev cert' -i localhost.crt
```

#### Mac Os
```shell
$ sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain localhost.crt
```

<a id="f-setup-https-locally" href="#a-setup-https-locally">1</a>. For further reference look [here](https://medium.com/@workockmoses/how-to-setup-https-for-local-development-on-ubuntu-with-self-signed-certificate-f97834064fd).

# Comandi utili

Comandi utili da utilizzare dopo l'avvio:

```
$ kubectl get deployments
$ kubectl delete deployment <deployment-name>
$ kubectl scale deployment <deployment-name> --replicas=0
$ kubectl scale deployment <deployment-name> --replicas=1
$ kubectl get pods
# controlla errori di k8s
$ kubectl describe pod <pod-name>
# controlla errori del servizio
$ kubectl logs -f <pod-name>
# eseguire comandi sul pod
$ kubectl exec -it <pod-name> bash
```
