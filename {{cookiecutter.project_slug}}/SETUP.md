# 🚚 Setup

Instructions to configure the Kubernetes cluster.

## 🧩 Requirements

### ☸️ Kubernetes

#### 📦 Package

Install the `kubectl` command-line tool:

- 🍏 macOS

  ```console
  $ brew install kubectl
  ```

- 🐧 GNU/Linux

  ```console
  $ sudo snap install kubectl --classic
  ```

### ☁️ DigitalOcean

#### 📦 Package

Install the `doctl` command-line tootl and authenticate:

- 🍏 macOS

  ```console
  $ brew install doctl
  ```

- 🐧 GNU/Linux

  ```console
  $ snap install doctl
  $ mkdir -p .kube
  $ sudo snap connect doctl:kube-config
  ```

#### 🔑 Authenticate

Use the `doctl` command-line tool to authenticate:

```console
$ doctl auth init --context {{cookiecutter.project_slug}}
$ doctl auth switch --context {{cookiecutter.project_slug}}
```

#### 🐍 Python packages

Install the `python-digitalocean` and `kubernetes` packages:

```console
$ python3 -m pip install python-digitalocean kubernetes
```

#### ✅ Token

A DigitalOcean user account is required by the setup procedure to configure the GitLab integration.

Put the DigitalOcean Access Token of the chosen user in an environment variable (e.g. export it in the command line or add it to the bash config).

**Note:** the access token can be generated from the DigitalOcean settings **"API -> Generate New Token"** section.
Beware that DigitalOcean only shows the token right after creation, and hides it thereafter.

```console
$ export DIGITALOCEAN_ACCESS_TOKEN=<your_digitalocean_access_token>
```

## 👣 Steps

### ☁️ DigitalOcean

To connect the project with the DigitalOcean hosted Kubernetes cluster, select an existing Kubernetes cluster on DigitalOcean or create a new one ( *Digitalocean > Create -> Clusters* ) and then execute the script:

```console
./scripts/do_setup.sh
```

### 🦝 GitLab

> WARNING: Step needed ONLY if you have NOT already done so in the previous step.

To connect GitLab with the DigitalOcean hosted Kubernetes cluster run the command :

```console
./scripts/add_cluster.sh
```

### ☸️ Kubernetes
{% set frontends = ["React"] %}
1. Change the host to the `k8s/develop/3_ingress.yaml` file and add the domain among the `ALLOWED_HOSTS` in `k8s/develop/2_secrets.yaml`
2. Check or change other variables in `k8s/develop/2_secrets.yaml`
3. Apply of the `development` directory with `kubectl apply -f k8s/development` (on all three projects the first commit must be done on `develop` GIT branch)
4. Create secret to allow the connection from Kubernetes to GitLab registry to download the built images (*get `<NAMESPACE>` from `k8s/develop/1_namespace.yaml`*):

    ```console
    $ python3 ./scripts/python/add_registry.py
    ```
5. Push a commit to the `develop` branch of {% if cookiecutter.which_frontend in frontends %}`frontend` (e.g. `src/client/index.html`) and {% endif %}`backend` (e.g. `{{cookiecutter.project_slug}}/settings.py`) to start the first CI/CD pipeline.

### 📃 Graphana logs
1. Make you sure to have a Graphana/Loki instance.
2. Create fluentd secret file from `k8s/cluster/fluentd/1_fluentd-secrets.yaml_template`.
    ```console
    $ cp k8s/cluster/fluentd/1_fluentd-secrets.yaml_template k8s/cluster/fluentd/1_fluentd-secrets.yaml
    ```
3. Change variables in `k8s/cluster/fluentd/1_fluentd-secrets.yaml` (E.g. `LOKI_URL` will be `http://<IP>:3100`).
4. Apply fluentd folder `kubectl apply -f k8s/cluster/fluentd`.
5. Apply kube-state-metrics `./scripts/kube-state-metrics_setup.sh`.
6. If it doesn't already exist, configure a `basic auth` for the k8s metrics ingress nginx as suggested [here](https://kubernetes.github.io/ingress-nginx/examples/auth/basic/)
7. Add a record A to DNS `metrics.{{ cookiecutter.project_domain }}` that point to k8s cluster IP.
8. Apply kube-state-metrics ingress `kubectl apply -f k8s/cluster/metrics_ingress.yaml`.
