# {{ cookiecutter.project_name }}

Platform repository for the **{{ cookiecutter.project_name }}** project.

This repo orchestrates the cloud infrastructure (Kubernetes cluster, core providers,
DNS, certificates, …) via the [Minos](https://gitlab.com/20tab-open/minos) platform
image. The application services live as sibling repositories cloned as nested
directories with their own `.git`.

## Layout

```
{{ cookiecutter.project_dirname }}/
├── .gitlab-ci.yml          # platform pipeline (core + kubernetes stages)
├── minos/
│   └── ${CLUSTER}/         # one folder per cluster (e.g. dev, main)
│       ├── core/
│       │   ├── aws.tfvars
│       │   └── digitalocean.tfvars
│       └── kubernetes.tfvars
├── vault-project.tfvars.example   # input for Phase A (admin) of vault-project
{% if cookiecutter.backend_type != 'none' %}├── {{ cookiecutter.backend_service_slug }}/      # backend service (own .git)
{% endif %}{% if cookiecutter.frontend_type != 'none' %}├── {{ cookiecutter.frontend_service_slug }}/     # frontend service (own .git)
{% endif %}└── README.md
```

The matrix in `.gitlab-ci.yml` runs core provisioning for **aws** and **digitalocean**
in parallel; tweak `CORE_PROVIDER` matrix or remove tfvars for providers you don't use.

## Prerequisites

This is a two-phase setup. Phase A is run once by an administrator, Phase B is the
GitLab pipeline that consumes the platform repo.

### Phase A — admin (one-off)

The admin runs the [`vault-project`](https://gitlab.com/20tab/vault/vault-project)
Terraform module to create per-project policies and identity entities on Vault. The
file `vault-project.tfvars.example` in this repo contains the values to use:

```shell
git clone https://gitlab.com/20tab/vault/vault-project.git
cd vault-project
cp /path/to/this/repo/vault-project.tfvars.example terraform.tfvars
# edit project_admin_users, project_namespace_path
terraform init
terraform apply
```

After Phase A the admin also seeds the per-project Vault secrets used by the
platform CI (DigitalOcean token, S3 credentials, TFC token).

### Phase B — platform pipeline

Required variables on the GitLab project (or the parent group):

| Variable                   | Notes                                                                     |
| -------------------------- | ------------------------------------------------------------------------- |
| `VAULT_ADDR`               | Vault address (e.g. `https://vault.20tab.com/`).                          |
| `TF_CLOUD_HOSTNAME`        | Defaults to `app.terraform.io`.                                           |
| `TF_CLOUD_ORGANIZATION`    | Set to `{{ cookiecutter.terraform_cloud_organization }}`.                 |
| `CLUSTER`                  | Set on pipeline trigger (e.g. `dev`, `main`).                             |

To provision a cluster, run a manual pipeline on `main` from the GitLab UI
(_Pipelines → Run pipeline_) with `CLUSTER=<cluster_slug>`. The pipeline iterates:

1. `core:plan` → `core:apply` (matrix on `CORE_PROVIDER`) reads
   `minos/${CLUSTER}/core/${CORE_PROVIDER}.tfvars` and applies via the
   `{{ cookiecutter.minos_platform_image }}` image.
2. `kubernetes:plan` → `kubernetes:apply` reads `minos/${CLUSTER}/kubernetes.tfvars`
   and consumes the outputs from `core:apply` via auto-loaded JSON tfvars.

Two kubernetes plan/apply variants are provided:

- `kubernetes-base` only applies `helm_release.traefik` and `helm_release.cert_manager`
  (bootstrap of routing + certs).
- `kubernetes-full` applies the full kubernetes stack.

The TFC workspace naming used:

- `${PROJECT_SLUG}_platform_${CLUSTER}_core_${CORE_PROVIDER}`
- `${PROJECT_SLUG}_platform_${CLUSTER}_kubernetes`

All workspaces live inside the TFC project named after `{{ cookiecutter.project_slug }}`
(execution mode `local`, inherited from the project).

## Services

Application services live in sibling directories, each as an independent GitLab
project with its own `.git`. They are bootstrapped from their own template repos
(see `django-continuous-delivery`, `nextjs-continuous-delivery`) and consume the
`{{ cookiecutter.minos_service_image }}` image at deploy time.

Each service repo lays out its own `minos/` directory with `common.tfvars` plus
per-environment `this.tfvars` and `shared-config.yaml`. Service workspaces on TFC
are named `${PROJECT_SLUG}_${SERVICE_SLUG}_${CI_ENVIRONMENT_SLUG}`.

## References

- Minos image registry: `registry.gitlab.com/20tab-open/minos/{platform,service}`
- OpenTofu CI component: `${CI_SERVER_FQDN}/components/opentofu/job-templates@{{ cookiecutter.opentofu_component_version }}`
- OpenTofu version: `{{ cookiecutter.opentofu_version }}`
