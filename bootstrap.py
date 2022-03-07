#!/usr/bin/env python
"""Initialize a web project Django service based on a template."""

import os
import re
import secrets
import shutil
import subprocess
from functools import partial
from pathlib import Path
from time import time

import click
import validators
from cookiecutter.main import cookiecutter
from slugify import slugify

BACKEND_TEMPLATE_URLS = {
    "django": "https://github.com/20tab/django-continuous-delivery"
}
BACKEND_TYPE_CHOICES = ["django", "none"]
DEFAULT_DIGITALOCEAN_DATABASE_CLUSTER_NODE_SIZE = "db-s-1vcpu-2gb"
DEFAULT_SERVICE_SLUG = "orchestrator"
DEPLOYMENT_TYPE_CHOICES = ["k8s-digitalocean", "k8s-other"]
DEPLOYMENT_TYPE_DEFAULT = "k8s-digitalocean"
ENVIRONMENTS_DISTRIBUTION_CHOICES = ["1", "2", "3"]
ENVIRONMENTS_DISTRIBUTION_PROMPT = """Choose the environments distribution:
  1 - All environments share the same stack (Default)
  2 - Dev and Stage environments share the same stack, Prod has its own
  3 - Each environment has its own stack
"""
ENVIRONMENTS_DISTRIBUTION_DEFAULT = "1"
DIGITALOCEAN_SPACES_REGION_DEFAULT = "fra1"
FRONTEND_TEMPLATE_URLS = {
    "nextjs": "https://github.com/20tab/react-ts-continuous-delivery"
}
FRONTEND_TYPE_CHOICES = ["nextjs", "none"]
GITLAB_TOKEN_ENV_VAR = "GITLAB_PRIVATE_TOKEN"
MEDIA_STORAGE_CHOICES = ["local", "s3-digitalocean", "none"]
MEDIA_STORAGE_DEFAULT = "s3-digitalocean"
OUTPUT_DIR = os.getenv("OUTPUT_DIR")
SUBREPOS_DIR = ".subrepos"

error = partial(click.style, fg="red")
highlight = partial(click.style, fg="cyan")
info = partial(click.style, dim=True)
warning = partial(click.style, fg="yellow")


def get_stacks_environments(
    environments_distribution,
    domain_prefix_dev,
    domain_prefix_stage,
    domain_prefix_prod,
    project_url_dev,
    project_url_stage,
    project_url_prod,
):
    """Return a dict with the environments distribution per stack."""
    dev_env = {
        "name": "Development",
        "url": project_url_dev,
        "prefix": domain_prefix_dev,
    }
    stage_env = {
        "name": "Staging",
        "url": project_url_stage,
        "prefix": domain_prefix_stage,
    }
    prod_env = {
        "name": "Production",
        "url": project_url_prod,
        "prefix": domain_prefix_prod,
    }
    if environments_distribution == "1":
        return {"main": {"dev": dev_env, "stage": stage_env, "prod": prod_env}}
    elif environments_distribution == "2":
        return {
            "dev": {"dev": dev_env, "stage": stage_env},
            "main": {"prod": prod_env},
        }
    elif environments_distribution == "3":
        return {
            "dev": {"dev": dev_env},
            "stage": {"stage": stage_env},
            "main": {"prod": prod_env},
        }
    return {}


def init_service(
    output_dir,
    project_name,
    project_slug,
    project_dirname,
    backend_type,
    backend_service_slug,
    backend_service_port,
    frontend_type,
    frontend_service_slug,
    frontend_service_port,
    media_storage,
    project_domain,
    stacks_environments,
    deployment_type,
):
    """Initialize the service."""
    click.echo(info("...cookiecutting the service"))
    cookiecutter(
        ".",
        extra_context={
            "backend_service_port": backend_service_port,
            "backend_service_slug": backend_service_slug,
            "backend_type": backend_type,
            "deployment_type": deployment_type,
            "frontend_service_port": frontend_service_port,
            "frontend_service_slug": frontend_service_slug,
            "frontend_type": frontend_type,
            "media_storage": media_storage,
            "project_dirname": project_dirname,
            "project_domain": project_domain,
            "project_name": project_name,
            "project_slug": project_slug,
            "stacks": stacks_environments,
        },
        output_dir=output_dir,
        no_input=True,
    )


def create_env_file(service_dir):
    """Create env file from the template."""
    click.echo(info("...generating the .env file"))
    env_path = Path(service_dir) / ".env_template"
    env_text = (
        env_path.read_text()
        .replace("__SECRETKEY__", secrets.token_urlsafe(40))
        .replace("__PASSWORD__", secrets.token_urlsafe(8))
    )
    (Path(service_dir) / ".env").write_text(env_text)


def init_gitlab(
    gitlab_group_slug,
    gitlab_private_token,
    gitlab_project_variables,
    gitlab_group_variables,
    gitlab_group_owners,
    gitlab_group_maintainers,
    gitlab_group_developers,
    project_name,
    project_slug,
    service_slug,
    service_dir,
    terraform_dir,
    logs_dir,
):
    """Initialize the Gitlab repositories."""
    click.echo(info("...creating the Gitlab repository and associated resources"))
    terraform_dir = Path(terraform_dir) / service_slug
    os.makedirs(terraform_dir, exist_ok=True)
    env = dict(
        TF_DATA_DIR=str((Path(terraform_dir) / "data").resolve()),
        TF_LOG="INFO",
        TF_VAR_gitlab_group_variables="{%s}"
        % ", ".join(f"{k} = {v}" for k, v in gitlab_group_variables.items()),
        TF_VAR_gitlab_group_slug=gitlab_group_slug,
        TF_VAR_gitlab_token=gitlab_private_token,
        TF_VAR_gitlab_group_developers=gitlab_group_developers,
        TF_VAR_gitlab_group_maintainers=gitlab_group_maintainers,
        TF_VAR_gitlab_group_owners=gitlab_group_owners,
        TF_VAR_project_name=project_name,
        TF_VAR_project_slug=project_slug,
        TF_VAR_gitlab_project_variables="{%s}"
        % ", ".join(f"{k} = {v}" for k, v in gitlab_project_variables.items()),
        TF_VAR_service_dir=service_dir,
        TF_VAR_service_slug=service_slug,
    )
    state_path = Path(terraform_dir) / "state.tfstate"
    cwd = Path("terraform")
    logs_dir = Path(logs_dir) / service_slug / "terraform"
    os.makedirs(logs_dir)
    init_log_path = logs_dir / "init.log"
    init_stdout_path = logs_dir / "init-stdout.log"
    init_stderr_path = logs_dir / "init-stderr.log"
    init_process = subprocess.run(
        [
            "terraform",
            "init",
            "-backend-config",
            f"path={state_path.resolve()}",
            "-input=false",
            "-no-color",
        ],
        capture_output=True,
        cwd=cwd,
        env=dict(**env, TF_LOG_PATH=str(init_log_path.resolve())),
        text=True,
    )
    init_stdout_path.write_text(init_process.stdout)
    if init_process.returncode == 0:
        apply_log_path = logs_dir / "apply.log"
        apply_stdout_path = logs_dir / "apply-stdout.log"
        apply_stderr_path = logs_dir / "apply-stderr.log"
        apply_process = subprocess.run(
            ["terraform", "apply", "-auto-approve", "-input=false", "-no-color"],
            capture_output=True,
            cwd=cwd,
            env=dict(**env, TF_LOG_PATH=str(apply_log_path.resolve())),
            text=True,
        )
        apply_stdout_path.write_text(apply_process.stdout)
        if apply_process.returncode != 0:
            apply_stderr_path.write_text(apply_process.stderr)
            click.echo(
                error(
                    "Error applying Terraform Gitlab configuration "
                    f"(check {apply_stderr_path} and {apply_log_path})"
                )
            )
            destroy_log_path = logs_dir / "destroy.log"
            destroy_stdout_path = logs_dir / "destroy-stdout.log"
            destroy_stderr_path = logs_dir / "destroy-stderr.log"
            destroy_process = subprocess.run(
                [
                    "terraform",
                    "destroy",
                    "-auto-approve",
                    "-input=false",
                    "-no-color",
                ],
                capture_output=True,
                cwd=cwd,
                env=dict(**env, TF_LOG_PATH=str(destroy_log_path.resolve())),
                text=True,
            )
            destroy_stdout_path.write_text(destroy_process.stdout)
            if destroy_process.returncode != 0:
                destroy_stderr_path.write_text(destroy_process.stderr)
                click.echo(
                    error(
                        "Error performing Terraform destroy "
                        f"(check {destroy_stderr_path} and {destroy_log_path})"
                    )
                )
            raise click.Abort()
    else:
        init_stderr_path.write_text(init_process.stderr)
        click.echo(
            error(
                "Error performing Terraform init "
                f"(check {init_stderr_path} and {init_log_path})"
            )
        )
        raise click.Abort()


def change_output_owner(service_dir, uid, gid):
    """Change the owner of the output directory recursively."""
    all((uid, gid)) and subprocess.run(["chown", "-R", f"{uid}:{gid}", service_dir])


def init_subrepo(service_slug, template_url, **options):
    """Initialize a subrepo using the given template and options."""
    subrepo_dir = str((Path(SUBREPOS_DIR) / service_slug).resolve())
    shutil.rmtree(subrepo_dir, ignore_errors=True)
    subprocess.run(
        [
            "git",
            "clone",
            template_url,
            subrepo_dir,
            "--branch",
            "feature/terraform",
            "-q",
        ],
    )
    options.update(
        project_dirname=service_slug,
        service_slug=service_slug,
    )
    subprocess.run(
        ["python", "-m", "pip", "install", "-r", "requirements/remote.txt"],
        cwd=subrepo_dir,
    )
    subprocess.run(
        ["python", "-c", f"from bootstrap import run; run(**{options})"],
        cwd=subrepo_dir,
    )


def run(
    uid,
    gid,
    output_dir,
    project_name,
    project_slug,
    project_dirname,
    service_slug,
    service_dir,
    backend_type,
    backend_service_slug,
    backend_service_port,
    frontend_type,
    frontend_service_slug,
    frontend_service_port,
    deployment_type,
    digitalocean_token,
    environments_distribution,
    project_domain,
    domain_prefix_dev,
    domain_prefix_stage,
    domain_prefix_prod,
    project_url_dev,
    project_url_stage,
    project_url_prod,
    digitalocean_k8s_cluster_region,
    digitalocean_database_cluster_region,
    digitalocean_database_cluster_node_size,
    sentry_org,
    sentry_url,
    sentry_auth_token,
    use_pact,
    pact_broker_url,
    pact_broker_username,
    pact_broker_password,
    media_storage,
    digitalocean_spaces_bucket_region,
    digitalocean_spaces_access_id,
    digitalocean_spaces_secret_key,
    use_gitlab,
    gitlab_private_token,
    gitlab_group_slug,
    gitlab_group_owners,
    gitlab_group_maintainers,
    gitlab_group_developers,
    terraform_dir,
    logs_dir,
):
    """Run the bootstrap."""
    run_id = f"{time():.0f}"
    terraform_dir = str(Path(terraform_dir or f".terraform/{run_id}").resolve())
    logs_dir = str(Path(logs_dir or f".logs/{run_id}").resolve())
    click.echo(highlight(f"Initializing the {service_slug} service:"))
    stacks_environments = get_stacks_environments(
        environments_distribution,
        domain_prefix_dev,
        domain_prefix_stage,
        domain_prefix_prod,
        project_url_dev,
        project_url_stage,
        project_url_prod,
    )
    init_service(
        output_dir,
        project_name,
        project_slug,
        project_dirname,
        backend_type,
        backend_service_slug,
        backend_service_port,
        frontend_type,
        frontend_service_slug,
        frontend_service_port,
        media_storage,
        project_domain,
        stacks_environments,
        deployment_type,
    )
    create_env_file(service_dir)
    if use_gitlab:
        gitlab_project_variables = {}
        gitlab_group_variables = dict(
            BACKEND_SERVICE_PORT='{value = "%s"}' % backend_service_port,
            FRONTEND_SERVICE_PORT='{value = "%s"}' % frontend_service_port,
        )
        project_domain and gitlab_group_variables.update(
            DOMAIN='{value = "%s"}' % project_domain
        )
        backend_service_slug and frontend_service_slug and (
            gitlab_group_variables.update(
                INTERNAL_BACKEND_URL='{value = "http://%s:%s"}'
                % (backend_service_slug, backend_service_port)
            )
        )
        sentry_org and gitlab_group_variables.update(
            SENTRY_ORG='{value = "%s"}' % sentry_org,
            SENTRY_URL='{value = "%s"}' % sentry_url,
            SENTRY_AUTH_TOKEN='{value = "%s", masked = true}' % sentry_auth_token,
        )
        if use_pact:
            pact_broker_auth_url = re.sub(
                r"^(https?)://(.*)$",
                fr"\g<1>://{pact_broker_username}:{pact_broker_password}@\g<2>",
                pact_broker_url,
            )
            gitlab_group_variables.update(
                PACT_ENABLED='{value = "true", protected = false}',
                PACT_BROKER_BASE_URL=(
                    '{value = "%s", protected = false}' % pact_broker_url
                ),
                PACT_BROKER_USERNAME=(
                    '{value = "%s", protected = false}' % pact_broker_username
                ),
                PACT_BROKER_PASSWORD=(
                    '{value = "%s", masked = true, protected = false}'
                    % pact_broker_password
                ),
                PACT_BROKER_AUTH_URL=(
                    '{value = "%s", masked = true, protected = false}'
                    % pact_broker_auth_url
                ),
            )
        media_storage == "s3-digitalocean" and gitlab_group_variables.update(
            DIGITALOCEAN_BUCKET_REGION=(
                '{value = "%s"}' % digitalocean_spaces_bucket_region
            ),
            S3_BUCKET_ENDPOINT_URL=(
                '{value = "https://%s.digitaloceanspaces.com"}'
                % digitalocean_spaces_bucket_region
            ),
            S3_BUCKET_ACCESS_ID=(
                '{value = "%s", masked = true}' % digitalocean_spaces_access_id
            ),
            S3_BUCKET_SECRET_KEY=(
                '{value = "%s", masked = true}' % digitalocean_spaces_secret_key
            ),
        )
        digitalocean_token and gitlab_group_variables.update(
            DIGITALOCEAN_TOKEN='{value = "%s", masked = true}' % digitalocean_token
        )
        if "digitalocean" in deployment_type:
            gitlab_project_variables.update(
                DIGITALOCEAN_K8S_CLUSTER_REGION='{value = "%s"}'
                % digitalocean_k8s_cluster_region,
                DIGITALOCEAN_DATABASE_CLUSTER_REGION='{value = "%s"}'
                % digitalocean_database_cluster_region,
                DIGITALOCEAN_DATABASE_CLUSTER_NODE_SIZE='{value = "%s"}'
                % digitalocean_database_cluster_node_size,
            )
        init_gitlab(
            gitlab_group_slug,
            gitlab_private_token,
            gitlab_project_variables,
            gitlab_group_variables,
            gitlab_group_owners,
            gitlab_group_maintainers,
            gitlab_group_developers,
            project_name,
            project_slug,
            service_slug,
            service_dir,
            terraform_dir,
            logs_dir,
        )
    common_options = {
        "uid": uid,
        "output_dir": service_dir,
        "project_name": project_name,
        "project_slug": project_slug,
        "project_url_dev": project_url_dev,
        "project_url_stage": project_url_stage,
        "project_url_prod": project_url_prod,
        "use_gitlab": use_gitlab,
        "gitlab_private_token": gitlab_private_token,
        "gitlab_group_slug": gitlab_group_slug,
    }
    backend_template_url = BACKEND_TEMPLATE_URLS.get(backend_type)
    if backend_template_url:
        init_subrepo(
            backend_service_slug,
            backend_template_url,
            internal_service_port=backend_service_port,
            logs_dir=logs_dir,
            media_storage=media_storage,
            terraform_dir=terraform_dir,
            **common_options,
        )
    frontend_template_url = FRONTEND_TEMPLATE_URLS.get(frontend_type)
    if frontend_template_url:
        init_subrepo(
            frontend_service_slug,
            frontend_template_url,
            internal_service_port=frontend_service_port,
            logs_dir=logs_dir,
            terraform_dir=terraform_dir,
            **common_options,
        )
    change_output_owner(service_dir, uid, gid)


def slugify_option(ctx, param, value):
    """Slugify an option value."""
    return value and slugify(value)


def validate_or_prompt_url(value, message, default=None, required=False):
    """Validate the given URL or prompt until a valid value is provided."""
    if value is not None:
        if not required and value == "" or validators.url(value):
            return value
        else:
            click.echo("Please type a valid URL!")
    new_value = click.prompt(message, default=default)
    return validate_or_prompt_url(new_value, message, default, required)


def validate_or_prompt_password(value, message, default=None, required=False):
    """Validate the given password or prompt until a valid value is provided."""
    if value is not None:
        if not required and value == "" or validators.length(value, min=8):
            return value
        else:
            click.echo("Please type at least 8 chars!")
    new_value = click.prompt(message, default=default, hide_input=True)
    return validate_or_prompt_password(new_value, message, default, required)


@click.command()
@click.option("--uid", type=int)
@click.option("--gid", type=int)
@click.option("--output-dir", default=".", required=OUTPUT_DIR is None)
@click.option("--project-name", prompt=True)
@click.option("--project-slug", callback=slugify_option)
@click.option("--project-dirname")
@click.option("--backend-type")
@click.option("--backend-service-slug")
@click.option("--backend-service-port", default=8000, type=int)
@click.option("--frontend-type")
@click.option("--frontend-service-slug")
@click.option("--frontend-service-port", default=3000, type=int)
@click.option(
    "--deployment-type",
    type=click.Choice(DEPLOYMENT_TYPE_CHOICES, case_sensitive=False),
)
@click.option("--digitalocean-token")
@click.option(
    "--environments-distribution",
    type=click.Choice(ENVIRONMENTS_DISTRIBUTION_CHOICES),
)
@click.option("--project-domain")
@click.option("--domain-prefix-dev")
@click.option("--domain-prefix-stage")
@click.option("--domain-prefix-prod")
@click.option("--project-url-dev")
@click.option("--project-url-stage")
@click.option("--project-url-prod")
@click.option("--digitalocean-k8s-cluster-region")
@click.option("--digitalocean-database-cluster-region")
@click.option("--digitalocean-database-cluster-node-size")
@click.option("--sentry-org")
@click.option("--sentry-url")
@click.option("--sentry-auth-token")
@click.option("--use-pact/--no-pact", is_flag=True, default=None)
@click.option("--pact-broker-url")
@click.option("--pact-broker-username")
@click.option("--pact-broker-password")
@click.option(
    "--media-storage",
    type=click.Choice(MEDIA_STORAGE_CHOICES, case_sensitive=False),
)
@click.option("--digitalocean-spaces-bucket-region")
@click.option("--digitalocean-spaces-access-id")
@click.option("--digitalocean-spaces-secret-key")
@click.option("--digitalocean-spaces-secret-key")
@click.option("--use-gitlab/--no-gitlab", is_flag=True, default=None)
@click.option("--gitlab-private-token", envvar=GITLAB_TOKEN_ENV_VAR)
@click.option("--gitlab-group-slug")
@click.option("--gitlab-group-owners", default="")
@click.option("--gitlab-group-maintainers", default="")
@click.option("--gitlab-group-developers", default="")
@click.option("--terraform-dir")
@click.option("--logs-dir")
def init_command(
    uid,
    gid,
    output_dir,
    project_name,
    project_slug,
    project_dirname,
    backend_type,
    backend_service_slug,
    backend_service_port,
    frontend_type,
    frontend_service_slug,
    frontend_service_port,
    deployment_type,
    digitalocean_token,
    environments_distribution,
    project_domain,
    domain_prefix_dev,
    domain_prefix_stage,
    domain_prefix_prod,
    project_url_dev,
    project_url_stage,
    project_url_prod,
    digitalocean_k8s_cluster_region,
    digitalocean_database_cluster_region,
    digitalocean_database_cluster_node_size,
    sentry_org,
    sentry_url,
    sentry_auth_token,
    use_pact,
    pact_broker_url,
    pact_broker_username,
    pact_broker_password,
    media_storage,
    digitalocean_spaces_bucket_region,
    digitalocean_spaces_access_id,
    digitalocean_spaces_secret_key,
    use_gitlab,
    gitlab_private_token,
    gitlab_group_slug,
    gitlab_group_owners,
    gitlab_group_maintainers,
    gitlab_group_developers,
    terraform_dir,
    logs_dir,
):
    """Collect options and run the bootstrap."""
    output_dir = OUTPUT_DIR or output_dir
    project_slug = slugify(
        project_slug or click.prompt("Project slug", default=slugify(project_name)),
    )
    project_dirname = slugify(project_slug, separator="")
    service_slug = DEFAULT_SERVICE_SLUG
    service_dir = str((Path(output_dir) / project_dirname).resolve())
    if Path(service_dir).is_dir() and click.confirm(
        warning(
            f'A directory "{service_dir}" already exists and '
            "must be deleted. Continue?",
        ),
        abort=True,
    ):
        shutil.rmtree(service_dir)
    backend_type = (
        backend_type in BACKEND_TYPE_CHOICES
        and backend_type
        or click.prompt(
            "Backend type",
            default=BACKEND_TYPE_CHOICES[0],
            type=click.Choice(BACKEND_TYPE_CHOICES, case_sensitive=False),
        )
    ).lower()
    if backend_type:
        backend_service_slug = slugify(
            backend_service_slug
            or click.prompt("Backend service slug", default="backend"),
            separator="",
        )
    frontend_type = (
        frontend_type in FRONTEND_TYPE_CHOICES
        and frontend_type
        or click.prompt(
            "Frontend type",
            default=FRONTEND_TYPE_CHOICES[0],
            type=click.Choice(FRONTEND_TYPE_CHOICES, case_sensitive=False),
        )
    ).lower()
    if frontend_type:
        frontend_service_slug = slugify(
            frontend_service_slug
            or click.prompt("Frontend service slug", default="frontend"),
            separator="",
        )
    deployment_type = (
        deployment_type in DEPLOYMENT_TYPE_CHOICES
        and deployment_type
        or click.prompt(
            "Deploy type",
            default=DEPLOYMENT_TYPE_DEFAULT,
            type=click.Choice(DEPLOYMENT_TYPE_CHOICES, case_sensitive=False),
        )
    ).lower()
    digitalocean_enabled = "digitalocean" in deployment_type
    if digitalocean_enabled:
        digitalocean_token = validate_or_prompt_password(
            digitalocean_token,
            "DigitalOcean token",
            required=True,
        )
    environments_distribution = (
        environments_distribution in ENVIRONMENTS_DISTRIBUTION_CHOICES
        and environments_distribution
        or click.prompt(
            ENVIRONMENTS_DISTRIBUTION_PROMPT,
            default=ENVIRONMENTS_DISTRIBUTION_DEFAULT,
            type=click.Choice(ENVIRONMENTS_DISTRIBUTION_CHOICES),
        )
    )
    if digitalocean_enabled:
        project_domain = project_domain or click.prompt(
            "Project domain (e.g. 20tab.com, "
            "if you prefer to skip DigitalOcean DNS configuration, leave blank)",
            default="",
        )
    if project_domain:
        domain_prefix_dev = domain_prefix_dev or click.prompt(
            "Development domain prefix",
            default="dev",
        )
        domain_prefix_stage = domain_prefix_stage or click.prompt(
            "Staging domain prefix",
            default="stage",
        )
        domain_prefix_prod = domain_prefix_prod or click.prompt(
            "Production domain prefix",
            default="www",
        )
        project_url_dev = f"https://{domain_prefix_dev}.{project_domain}"
        project_url_stage = f"https://{domain_prefix_stage}.{project_domain}"
        project_url_prod = f"https://{domain_prefix_prod}.{project_domain}"
    else:
        project_domain = ""
        domain_prefix_dev = domain_prefix_stage = domain_prefix_prod = ""
        project_url_dev = validate_or_prompt_url(
            project_url_dev,
            "Development environment complete URL",
            default=f"https://dev.{project_slug}.com/",
        )
        project_url_stage = validate_or_prompt_url(
            project_url_stage,
            "Staging environment complete URL",
            default=f"https://stage.{project_slug}.com/",
        )
        project_url_prod = validate_or_prompt_url(
            project_url_prod,
            "Production environment complete URL",
            default=f"https://www.{project_slug}.com/",
        )
    sentry_org = sentry_org or click.prompt(
        'Sentry organization (e.g. "20tab", leave blank if unused)',
        default="",
    )
    if digitalocean_enabled:
        # TODO: ask these settings for each stack
        digitalocean_k8s_cluster_region = (
            digitalocean_k8s_cluster_region
            or click.prompt("Kubernetes cluster Digital Ocean region", default="fra1")
        )
        digitalocean_database_cluster_region = (
            digitalocean_database_cluster_region
            or click.prompt("Database cluster Digital Ocean region", default="fra1")
        )
        digitalocean_database_cluster_node_size = (
            digitalocean_database_cluster_node_size
            or click.prompt(
                "Database cluster node size",
                default=DEFAULT_DIGITALOCEAN_DATABASE_CLUSTER_NODE_SIZE,
            )
        )
    if sentry_org:
        sentry_url = validate_or_prompt_url(
            sentry_url,
            "Sentry URL",
            default="https://sentry.io/",
            required=True,
        )
        sentry_auth_token = validate_or_prompt_password(
            sentry_auth_token,
            "Sentry auth token",
            required=True,
        )
    use_pact = (
        use_pact
        if use_pact is not None
        else click.confirm(warning("Do you want to configure Pact?"), default=True)
    )
    if use_pact:
        pact_broker_url = validate_or_prompt_url(
            pact_broker_url,
            "Pact broker URL (e.g. https://broker.20tab.com/)",
            required=True,
        )
        pact_broker_username = pact_broker_username or click.prompt(
            "Pact broker username",
        )
        pact_broker_password = validate_or_prompt_password(
            pact_broker_password,
            "Pact broker password",
            required=True,
        )
    media_storage = (
        media_storage
        or click.prompt(
            "Media storage",
            default=MEDIA_STORAGE_DEFAULT,
            type=click.Choice(MEDIA_STORAGE_CHOICES, case_sensitive=False),
        )
    ).lower()
    use_gitlab = (
        use_gitlab
        if use_gitlab is not None
        else click.confirm(warning("Do you want to configure Gitlab?"), default=True)
    )
    if use_gitlab:
        gitlab_group_slug = gitlab_group_slug or click.prompt(
            "Gitlab group slug", default=project_slug
        )
        click.confirm(
            warning(
                f'Make sure the Gitlab "{gitlab_group_slug}" group exists '
                "before proceeding. Continue?"
            ),
            abort=True,
        )
        gitlab_private_token = gitlab_private_token or click.prompt(
            "Gitlab private token (with API scope enabled)", hide_input=True
        )
        gitlab_group_owners = gitlab_group_owners or click.prompt(
            "Comma-separated Gitlab group owners", default=""
        )
        gitlab_group_maintainers = gitlab_group_maintainers or click.prompt(
            "Comma-separated Gitlab group maintainers", default=""
        )
        gitlab_group_developers = gitlab_group_developers or click.prompt(
            "Comma-separated Gitlab group developers", default=""
        )
        if media_storage == "s3-digitalocean":
            digitalocean_token = validate_or_prompt_password(
                digitalocean_token,
                "DigitalOcean token",
                required=True,
            )
            digitalocean_spaces_bucket_region = (
                digitalocean_spaces_bucket_region
                or click.prompt(
                    "DigitalOcean Spaces region",
                    default=DIGITALOCEAN_SPACES_REGION_DEFAULT,
                )
            )
            digitalocean_spaces_access_id = validate_or_prompt_password(
                digitalocean_spaces_access_id,
                "DigitalOcean Spaces Access Key ID",
                required=True,
            )
            digitalocean_spaces_secret_key = validate_or_prompt_password(
                digitalocean_spaces_secret_key,
                "DigitalOcean Spaces Secret Access Key",
                required=True,
            )
    run(
        uid,
        gid,
        output_dir,
        project_name,
        project_slug,
        project_dirname,
        service_slug,
        service_dir,
        backend_type,
        backend_service_slug,
        backend_service_port,
        frontend_type,
        frontend_service_slug,
        frontend_service_port,
        deployment_type,
        digitalocean_token,
        environments_distribution,
        project_domain,
        domain_prefix_dev,
        domain_prefix_stage,
        domain_prefix_prod,
        project_url_dev,
        project_url_stage,
        project_url_prod,
        digitalocean_k8s_cluster_region,
        digitalocean_database_cluster_region,
        digitalocean_database_cluster_node_size,
        sentry_org,
        sentry_url,
        sentry_auth_token,
        use_pact,
        pact_broker_url,
        pact_broker_username,
        pact_broker_password,
        media_storage,
        digitalocean_spaces_bucket_region,
        digitalocean_spaces_access_id,
        digitalocean_spaces_secret_key,
        use_gitlab,
        gitlab_private_token,
        gitlab_group_slug,
        gitlab_group_owners,
        gitlab_group_maintainers,
        gitlab_group_developers,
        terraform_dir,
        logs_dir,
    )


if __name__ == "__main__":
    init_command()
