# 20tab standard project

This is the [20tab](https://www.20tab.com/) standard project [cookiecutter](https://github.com/cookiecutter/cookiecutter) template.

## Documentation <!-- omit in toc -->

- [20tab standard project](#20tab-standard-project)
  - [Conventions](#conventions)
  - [Workspace initialization](#workspace-initialization)
    - [Python packages](#python-packages)
    - [Kubernetes](#kubernetes)
      - [MacOS](#mac-os-1)
      - [Linux](#linux-1)
    - [GitLab](#gitlab)
    - [Digital Ocean](#digitalocean)
      - [Mac OS](#mac-os-2)
      - [Linux](#linux-2)
  - [Usage](#usage)
    - [Cookiecutter](#cookiecutter)
    - [DigitalOcean setup](#digitalocean-setup)
    - [Kubernetes and GitLab connection](#kubernetes-and-gitlab-connection)
    - [Kubernetes apply](#kubernetes-apply)
      - [Warning](#warning)

## Conventions

In the following instructions, replace:

- `project_name` with your chosen project name

## Workspace initialization

### Python

The `cookiecutter` package must be installed in the active python environment in order to create and initialize the project structure.

```shell
$ pip install --user cookiecutter
```

### Kubernetes

Install the `kubectl` command-line tool, if the Kubernetes integration is needed.

#### Mac OS

```shell
$ brew install kubectl
```

#### Linux

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
Install the `python-digitalocean` package, if the DigitalOcean integration is needed.

```shell
$ pip install --user python-digitalocean
```

Put the DigitalOcean Access Token of the chosen user in an environment variable (e.g. export it in the command line or add it to the bash config).

```shell
$ export DIGITALOCEAN_ASCESS_TOKEN={{digitalocean_access_token}}
```

#### Mac OS

```shell
$ brew install doctl
$ doctl auth init
```

#### Linux

```shell
$ snap install doctl
$ sudo snap connect doctl:kube-config
$ doctl auth init
```

## Usage

This section shows how to create and initialize a project.

### Cookiecutter

Run the Cookiecutter command in the desired location, and follow the guided procedure:

```shell
$ cookiecutter https://github.com/20tab/20tab-standard-project
project_name [20tab standard project]: My project name
project_slug [myprojectname]:
use_gitlab [y]:
Choose the gitlab group name [project_name]:
Insert the usernames of all users you want to add to the group, separated by comma:
$ cd project_slug
```

---

# WIP

### DigitalOcean setup

- Create a Kubernetes cluster on DigitalOcean **Create -> Clusters**
- Create a token in the **API -> Generate New Token** section or select an existing one
- Run ./scripts/do_setup.sh

### Kubernetes and GitLab connection

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
    Name:         gitlab-admin-token-a0bc1
    Namespace:    kube-system
    Labels:       <none>
    Annotations:  kubernetes.io/service-account.name=gitlab-admin
                kubernetes.io/service-account.uid=abcd01ef-23gh-45i6-78j9-012klm34n5o6

    Type:  kubernetes.io/service-account-token

    Data
    ====
    ca.crt:     1025 bytes
    namespace:  11 bytes
    token:      <authentication_token>
  ```

- Assicurarsi di rimuovere la spunta da gitlab-managed cluster
- Salvare le impostazioni su gitlab

### Kubernetes apply

- Run `kubectl create secret docker-registry regcred --docker-server=http://registry.gitlab.com --docker-username=gitlab-20tab --docker-password=<PASSWORD> --docker-email=gitlab@20tab.com --namespace=<NAMESPACE>`
- Modificare l'host sul file `ingress.yaml` e aggiungere il dominio tra gli allowed_hosts in `secrets.yaml`
- Apply della cartella `kubectl apply -f k8s/development` (su tutti e tre i progetti il primo commit si deve fare su develop)
- Git push su frontend e backend (su develop)
