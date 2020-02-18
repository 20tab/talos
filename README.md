# 20tab standard project

This is the [20tab](https://www.20tab.com/) standard project [cookiecutter](https://github.com/cookiecutter/cookiecutter) template.

## Documentation <!-- omit in toc -->

- [20tab standard project](#20tab-standard-project)
  - [Conventions](#conventions)
  - [Workspace initialization](#workspace-initialization)
    - [Basic requirements](#basic-requirements)
      - [Python packages](#python-packages)
      - [Digital Ocean](#digital-ocean)
        - [OSX](#osx)
        - [Linux](#linux)
      - [Kubernetes](#kubernetes)
        - [OSX](#osx-1)
        - [Linux](#linux-1)
      - [GitLab](#gitlab)
  - [New project](#new-project)
    - [Creation](#creation)
  - [WIP](#wip)
    - [Digital Ocean setup](#digital-ocean-setup)
    - [Kubernetes and GitLab connection](#kubernetes-and-gitlab-connection)
    - [Kubernetes apply](#kubernetes-apply)
      - [Warning](#warning)
  - [Useful commands](#useful-commands)

## Conventions

In the following instructions:

- replace `projects` with your actual projects directory
- replace `project_name` with your chosen project name

## Workspace initialization

### Basic requirements

#### Python packages

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

**Note:** the access token can be generated from the GitLab settings "Access Tokens"
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

**Note:** in order to make the subsequent commands work, make sure to add at least the
username of the local user to the members list.

---

## WIP

### Digital Ocean setup

- Prima di tutto bisogna fare una volta nella vita il login con il comando:
    - docker login http://registry.gitlab.com --username=DO_GITLAB_USERNAME --password=DO_GITLAB_PASSWORD

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

- Modificare l'host sul file `ingress.yaml` e aggiungere il dominio tra gli allowed_hosts in `secrets.yaml`
- Apply della cartella `kubectl apply -f k8s/development` (su tutti e tre i progetti il primo commit si deve fare su develop)
- Git push su frontend e backend (su develop)

#### Warning

Fare attenzione ad i nomi molto lunghi:

```python
Error from server (Invalid): error when creating "k8s/development/ingress.yaml": Ingress.extensions "development-verylongprojectname2020-ingress-service" is invalid: spec.rules[0].http.backend.serviceName: Invalid value: "development-verylongprojectname2020-static-nginx-cluster-ip-service": must be no more than 63 characters
Error from server (Invalid): error when creating "k8s/development/staticfiles.yaml": Service "development-verylongprojectname2020-static-nginx-cluster-ip-service" is invalid: metadata.name: Invalid value: "development-verylongprojectname2020-static-nginx-cluster-ip-service": must be no more than 63 characters
```

## Useful commands

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
