# Talos

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)

> A [20tab](https://www.20tab.com/) standard project.

## 🧩 Requirements

The Talos script can be run either using Docker or as a local shell command.

### 🐋 Docker

In order to run Talos via Docker, a working [Docker installation](https://docs.docker.com/get-docker/) is the only requirement.

### 👨‍💻 Shell command

In order to run Talos as a shell command, first clone the repository in a local projects directory
```console
cd ~/projects
git clone https://github.com/20tab/20tab-standard-project.git talos
```
Then, install the following requirements
| Requirements | Instructions |
|--|--|
|🌎 Terraform  | [Install Guide](https://learn.hashicorp.com/tutorials/terraform/install-cli)  |
|🐍 Python Dependencies | `pip install -r talos/requirements/common.txt` |

## 🔑 Credentials

### 🌊 DigitalOcean
If DigitalOcean is chosen for deployment, a Personal Access Token with _write_ permission is required.<br/>
Additionally, if DigitalOcean Spaces is the chosen media storage backend, a pair of S3 access keys is required.
[DigitalOcean API Slugs](https://slugs.do-api.dev/)

**Note:** all credentials can be generated in the DigitalOcean API configuration section.<br/>
⚠️ Beware that the token is shown only once after creation.

### 🦊 GitLab
If the GitLab integration is enabled, a Personal Access Token with _api_ permission is required.<br/>
It can be generated in the GitLab User Settings panel.

**Note:** the token can be generated in the Access Tokens section of the GitLab User Settings panel.<br/>
⚠️ Beware that the token is shown only once after creation.

## 🚀️ Quickstart

Change to the projects directory, for example
```console
cd ~/projects
```

### 🐋 Docker

```console
docker run --interactive --tty --rm --volume $PWD:/data 20tab/talos:latest
```

### 👨‍💻 Shell command

```console
./talos/setup.py
```

### Example
```console
Project name: My Project Name
Project slug [my-project-name]:
Backend type (django, none) [django]:
Backend service slug [backend]:
Frontend type (nextjs, none) [nextjs]:
Frontend service slug [frontend]:
Choose the environments distribution:
  1 - All environments share the same stack (Default)
  2 - Dev and Stage environments share the same stack, Prod has its own
  3 - Each environment has its own stack
 (1, 2, 3) [1]:
Deploy type (digitalocean-k8s, other-k8s) [digitalocean-k8s]:
DigitalOcean token:
Project domain (e.g. 20tab.com, if you prefer to skip DigitalOcean DNS configuration, leave blank) []:
Development environment complete URL [https://dev.my-project-name.com]:
Staging environment complete URL [https://stage.my-project-name.com]:
Production environment complete URL [https://www.my-project-name.com]:
Kubernetes cluster DigitalOcean region [fra1]:
Database cluster DigitalOcean region [fra1]:
Database cluster node size [db-s-1vcpu-2gb]:
Do you want to configure Redis? [y/N]:
Sentry organization (e.g. "20tab", leave blank if unused) []:
Do you want to enable the monitoring stack? [y/N]:
Do you want to configure Pact? [Y/n]: n
Media storage (digitalocean-s3, aws-s3, local, none) [digitalocean-s3]:
Do you want to configure GitLab? [Y/n]:
GitLab group slug [my-project-name]:
Make sure the GitLab "my-project-name" group exists before proceeding. Continue? [y/N]: y
GitLab private token (with API scope enabled):
Comma-separated GitLab group owners []:
Comma-separated GitLab group maintainers []:
Comma-separated GitLab group developers []:
DigitalOcean Spaces region [fra1]:
DigitalOcean Spaces Access Key ID:
DigitalOcean Spaces Secret Access Key:
Initializing the orchestrator service:
...cookiecutting the service
...generating the .env file
...creating the GitLab repository and associated resources
Initializing the backend service:
...cookiecutting the service
...generating the .env file
...formatting the cookiecut python code
...compiling the requirements files
	- common.txt
	- test.txt
	- local.txt
	- remote.txt
	- base.txt
...creating the '/static' directory
...creating the GitLab repository and associated resources
Initializing the frontend service:
...cookiecutting the service
...generating the .env file
...creating the GitLab repository and associated resources
```
## 🗒️ Arguments

The following arguments can be appended to the Docker and shell commands

#### User id
`--uid=$UID`

#### Group id
`--gid=1000`

#### Output directory
`--output-dir="~/projects"`

#### Project name
`--project-name="My project name"`

#### Project slug
`--project-slug="my-project-name"`

#### Project dirname
`--project-dirname="myprojectname"`

### 🎖️ Services

#### Backend type
Value | Description | Argument
------------- | ------------- | -------------
django | https://github.com/20tab/django-continuous-delivery | `--backend-type=django`
none | the backend service will not be initialized | `--backend-type=none`

#### Backend service slug
`--backend-service-slug=backend`

#### Backend service port
`--backend-service-port=8000`

#### Frontend type
Value | Description | Argument
------------- | ------------- | -------------
nextjs | https://github.com/20tab/react-ts-continuous-delivery | `--frontend-type=nextjs`
none | the frontend service will not be initialized | `--frontend-type=none`

#### Frontend service slug
`--frontend-service-slug=frontend`

#### Frontend service port
`--frontend-service-port=3000`

### 📐 Architecture

#### Environment distribution
Choose the environments distribution:
Value  | Description | Argument
------------- | ------------- | -------------
1  | All environments share the same stack (Default) | `--environment-distribution=1`
2  | Dev and Stage environments share the same stack, Prod has its own | `--environment-distribution=2`
3  | Each environment has its own stack | `--environment-distribution=3`

#### Deploy type
Value  | Description | Argument
------------- | ------------- | -------------
digitalocean-k8s  | It will use the DigitalOcean | `--deployment-type=digitalocean-k8s`
other-k8s  | The configuration is custom and must be done manually | `--deployment-type=other-k8s`

#### Project Domain
If you don't want DigitalOcean DNS configuration the following args are required

`--project-url-dev=https://dev.project-domain.com`<br/>
`--project-url-stage=https://stage.project-domain.com`<br/>
`--project-url-prod=https://www.project-domain.com`

#### Media storage

Value  | Description | Argument
------------- | ------------- | -------------
digitalocean-s3  | DigitalOcean Spaces are used to store media | [DigitalOcean Media storage](#media-storage)
aws-s3  | AWS S3 are used to store media | `--media-storage=aws-s3`
local  | Docker Volume are used to store media | `--media-storage=local`
none  | Project have no media | `--media-storage=none`

### 🌊 DigitalOcean

#### DigitalOcean Token
`--digitalocean-token={{digitalocean-token}}`

#### Media storage
`--media-storage=digitalocean-s3`<br/>
`--spaces-bucket-region=fra1`<br/>
`--spaces-access-id`<br/>
`--spaces-secret-key`

#### Project Domain
If you want DigitalOcean DNS configuration the following args are required

`--project-domain=project-domain.com`<br/>
`--domain-prefix-dev=dev`<br/>
`--domain-prefix-stage=test`<br/>
`--domain-prefix-prod=www`

#### Kubernetes cluster DigitalOcean region
`"--digitalocean-k8s-cluster-region=fra1`

#### Database cluster DigitalOcean region
`"--digitalocean-database-cluster-region=fra1`

#### Database cluster DigitalOcean node size
`"--digitalocean-database-cluster-node-size=db-s-1vcpu-2gb`

#### Monitoring
For enabling monitoring the following arguments are needed:

if project domain is managed use

`--domain-prefix-monitoring=logs`

else use

`--project-url-monitoring=https://logs.example.org/`

#### Redis
For enabling redis integration the following arguments are needed:

`--use-redis`<br/>
`--digitalocean-redis-cluster-region=fra1`<br/>
`--digitalocean-redis-cluster-node-size=db-s-1vcpu-2gb`

Disabled args
`--no-redis`

### 🦊 GitLab
> **⚠️ Important:  Make sure the GitLab group exists before creating.**
> https://gitlab.com/gitlab-org/gitlab/-/issues/244345

For enabling gitlab integration the following arguments are needed:

`--gitlab-private-token={{gitlab-private-token}}`<br/>
`--gitlab-group-slug={{gitlab-group-slug}}`

Add user to repository using comma separeted arguments

`--gitlab-group-owners=user1, user@example.org`<br/>
`--gitlab-group-maintainers=user1, user@example.org`<br/>
`--gitlab-group-developers=user1, user@example.org`

#### 👨‍⚖️ Pact
For enabling pact the following arguments are needed:

`--pact-broker-url={{pact-broker-url}}`<br/>
`--pact-broker-username={{pact-broker-username}}`<br/>
`--pact-broker-password={{pact-broker-password}}`

#### 🪖 Sentry
For enabling sentry integration the following arguments are needed:

`--sentry-url=https://sentry.io/`<br/>
`--sentry-org={{sentry-org}}`<br/>
`--sentry-auth-token={{sentry-auth-token}}`

If the project has a backend service, the following argument is needed:

`--backend-sentry-dsn={{backend-sentry-dsn}}`

If the project has a frontend service, the following argument is needed:

`--frontend-sentry-dsn={{frontend-sentry-dsn}}`

#### 🔇 Quiet
No confirmations shown.

`--quiet`
