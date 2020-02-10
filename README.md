# 20tab standard project

This is the [20tab](https://www.20tab.com/) standard project template based on [cookiecutter](https://github.com/cookiecutter/cookiecutter).

## Outline

* [Basic requirements](#basic-requirements)
* [Setup a new project](#setup-a-new-project)
    * [Start Project](#start-project)

## Basic requirements

**Cookiecutter** must be installed before initializing the project.

```shell
$ pip install --user cookiecutter
```

## Setup a new project

This section explains the first steps when you need to create a new project.

### Start Project

Change directory and start a new project with this template:

```shell
$ cd ~/projects/
$ cookiecutter git@github.com:20tab/django-continuous-delivery.git
project_name [20tab standard project]: devopsproj
project_slug [devopsproj]:
$ cd devopsproj
```

---

## WIP

### Requirements
- doctl cli:
    - Mac: brew install doctl
    - Linux: snap install doctl
- kubectl cli:
  - Mac: brew install kubectl
  - Linux: snap install kubectl

### Setup repositories su gitlab.com

- Creazione nuovo gruppo: https://gitlab.com/groups/new (fare un check per capire se il nome del gruppo è stato già usato)
- Settare il nome e lo slug del gruppo utilizzando project_name e project_slug
- Creazione nuovo progetto (nel gruppo appena creato) con `project_name = "orchestrator"`
- Creazione nuovo progetto (nel gruppo appena creato) con `project_name = "backend"`
- Creazione nuovo progetto (nel gruppo appena creato) con `project_name = "frontend"`
- Inizializzare le 3 cartelle `git init` e `git remote add origin <url>`
- Creare il link del registro composto da `registry.gitlab.com` + `slug_progetto` + `slug_repo` e aggiungerlo in `backend.yaml` e `frontend.yaml` dei vari ambienti.
- Aggiungiamo i membri al gruppo (anche @gitlab-20tab) come owners

### Configurazione cluster digitalocean
- Creare un cluster k8s su digitalocean
- Creare un token nella sezione **API -> Generate New Token**
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
  - Lista dei secrets: `kubectl get secrets`, dovrebbe essere simile a `default-token-xxxxx`
  - Mostra il certificato: `kubectl get secret <secret name> -o jsonpath="{['data']['ca\.crt']}" | base64 --decode`
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
- Salvare le impostazioni su gitlab

### Apply dell'orchestratore
- Modificare l'host sul file `ingress.yaml` e aggiungere il dominio tra gli allowed_hosts in `secrets.yaml`
- Apply della cartella `kubectl apply -f k8s/development` (su tutti e tre i progetti il primo commit si deve fare su develop)
- Git push su frontend e backend (su develop)
