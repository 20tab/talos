# 20tab standard project

This is the [20tab](https://www.20tab.com/) standard project template based on [cookiecutter](https://github.com/cookiecutter/cookiecutter).

## Outline

* [Conventions](#conventions)
* [Workspace initialization](#workspace-initialization)
    * [Basic requirements](#basic-requirements)
* [Setup a new project](#setup-a-new-project)
    * [Start Project](#start-project)

## Conventions

- replace `projects` with your actual projects directory

- replace `project_name` with your chosen project name

## Workspace initialization

### Basic requirements

**Cookiecutter** must be installed before initializing the project.

```shell
$ pip install --user cookiecutter
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

## Setup a new project

This section explains the first steps when you need to create a new project.

### Start Project

Change directory and start a new project with this template:

```shell
$ cd ~/projects/
$ export GITLAB_PRIVATE_TOKEN={{gitlab_private_token}}
$ cookiecutter https://github.com/20tab/20tab-standard-project
project_name [20tab standard project]: project_name
project_slug [project_name]:
$ cd project_name
```

---

## WIP

### Setup repositories su gitlab.com

- TODO: creare di default il branch develop
- Inizializzare le 3 cartelle `git init` e `git remote add origin <url>`
- Aggiungiamo i membri al gruppo (anche @gitlab-20tab) come owners

### Configurazione cluster digitalocean

- Creare un cluster k8s su digitalocean **Create -> Clusters**
- Creare un token nella sezione **API -> Generate New Token** o usare uno esistente
- Login `doctl auth init` con il token
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

# Comandi utili

Comandi utili da utilizzare dopo l'avvio:

```
$ kubectl get deployments
$ kubectl delete deployment <deployment-name>
$ kubectl get pods
# controlla errori di k8s
$ kubectl describe pod <pod-name>
# controlla errori del servizio
$ kubectl logs -f <pod-name>
# eseguire comandi sul pod
$ kubectl exec -it <pod-name> bash
```