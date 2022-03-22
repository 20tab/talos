# 🚚 Setup

Instructions to configure the Kubernetes cluster.

## 🧩 Requirements

### ☸️ Kubernetes

#### 📦 Package

Install the `kubectl` command-line tool:

-   🍏 macOS

    ```console
    $ brew install kubectl
    ```

-   🐧 GNU/Linux

    ```console
    $ sudo snap install kubectl --classic
    ```

### ☁️ DigitalOcean

#### 📦 Package

Install the `doctl` command-line tootl and authenticate:

-   🍏 macOS

    ```console
    $ brew install doctl
    ```

-   🐧 GNU/Linux

    ```console
    $ snap install doctl
    $ mkdir -p .kube
    $ sudo snap connect doctl:kube-config
    ```

#### 🔑 Authenticate

Use the `doctl` command-line tool to authenticate:

```console
$ doctl auth init --context {{ cookiecutter.project_slug }}
$ doctl auth switch --context {{ cookiecutter.project_slug }}
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

To connect the project with the DigitalOcean hosted Kubernetes cluster, select an existing Kubernetes cluster on DigitalOcean or create a new one ( _Digitalocean > Create -> Clusters_ ) and then execute the script:

```console
./scripts/do_setup.sh
```

### 🦝 GitLab

> WARNING: Step needed ONLY if you have NOT already done so in the previous step.

To connect GitLab with the DigitalOcean hosted Kubernetes cluster run the command :

```console
./scripts/add_cluster.sh
```

# TODO Write section on K8s managed using GitLab env variables

### ☸️ Kubernetes

### 📃 Graphana logs

1. Make you sure to have a Graphana/Loki instance.
2. Create fluentd secret file from `k8s/cluster/fluentd/1_fluentd-secrets.yaml_template`.
    ```console
    $ cp k8s/cluster/fluentd/1_fluentd-secrets.yaml_template k8s/cluster/fluentd/1_fluentd-secrets.yaml
    ```
3. Change variables in `k8s/cluster/fluentd/1_fluentd-secrets.yaml` (E.g. `LOKI_URL` will be `http://<IP>:3100`).
4. Apply fluentd folder `kubectl apply -f k8s/cluster/fluentd`.
