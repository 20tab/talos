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
from cookiecutter.main import cookiecutter

from bootstrap.constants import (
    BACKEND_TEMPLATE_URLS,
    DEPLOYMENT_TYPE_CHOICES,
    ENVIRONMENT_DISTRIBUTION_CHOICES,
    FRONTEND_TEMPLATE_URLS,
    GITLAB_TOKEN_ENV_VAR,
    MEDIA_STORAGE_CHOICES,
    SUBREPOS_DIR,
)
from bootstrap.helpers import slugify_option
from bootstrap.options import (
    get_backend_service_slug,
    get_backend_type,
    get_broker_data,
    get_cluster_data,
    get_digitalocean_media_storage_data,
    get_digitalocean_token,
    get_environment_distribution,
    get_frontend_service_slug,
    get_frontend_type,
    get_gitlab_group_data,
    get_is_digitalocean_enabled,
    get_media_storage,
    get_output_dir,
    get_project_dirname,
    get_project_domain,
    get_project_slug,
    get_project_urls,
    get_sentry_org,
    get_sentry_token,
    get_sentry_url,
    get_service_dir,
    get_service_slug,
    get_use_gitlab,
    get_use_pact,
)

error = partial(click.style, fg="red")
highlight = partial(click.style, fg="cyan")
info = partial(click.style, dim=True)
warning = partial(click.style, fg="yellow")


def get_stacks_environments(
    environment_distribution,
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
    if environment_distribution == "1":
        return {"main": {"dev": dev_env, "stage": stage_env, "prod": prod_env}}
    elif environment_distribution == "2":
        return {
            "dev": {"dev": dev_env, "stage": stage_env},
            "main": {"prod": prod_env},
        }
    elif environment_distribution == "3":
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


def change_output_owner(service_dir, uid):
    """Change the owner of the output directory recursively."""
    uid is not None and subprocess.run(["chown", "-R", uid, service_dir])


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
        ["python", "-c", f"from bootstrap.bootstrap import run; run(**{options})"],
        cwd=subrepo_dir,
    )


def run(
    uid,
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
    environment_distribution,
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
        environment_distribution,
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
                rf"\g<1>://{pact_broker_username}:{pact_broker_password}@\g<2>",
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
    change_output_owner(service_dir, uid)


@click.command()
@click.option("--uid", type=int)
@click.option("--output-dir", default=".", required=os.getenv("OUTPUT_DIR") is None)
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
    "--environment-distribution", type=click.Choice(ENVIRONMENT_DISTRIBUTION_CHOICES)
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
    environment_distribution,
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
    output_dir = get_output_dir(output_dir)
    project_slug = get_project_slug(project_name, project_slug)
    project_dirname = get_project_dirname(project_slug)
    service_slug = get_service_slug()
    service_dir = get_service_dir(output_dir, project_dirname)
    backend_type = get_backend_type(backend_type)
    backend_service_slug = get_backend_service_slug(backend_service_slug, backend_type)
    frontend_type = get_frontend_type(frontend_service_slug, backend_type)
    frontend_service_slug = get_frontend_service_slug(
        frontend_service_slug, frontend_type
    )
    digitalocean_enabled = get_is_digitalocean_enabled(deployment_type)
    if digitalocean_enabled:
        digitalocean_token = get_digitalocean_token(digitalocean_token)
    environment_distribution = get_environment_distribution(environment_distribution)
    if digitalocean_enabled:
        project_domain = get_project_domain(project_domain)
    (
        project_domain,
        project_url_dev,
        project_url_stage,
        project_url_prod,
    ) = get_project_urls(
        project_slug,
        project_domain,
        domain_prefix_dev,
        domain_prefix_stage,
        domain_prefix_prod,
        project_url_dev,
        project_url_stage,
        project_url_prod,
    )
    sentry_org = get_sentry_org(sentry_org)
    if digitalocean_enabled:
        (
            digitalocean_k8s_cluster_region,
            digitalocean_database_cluster_region,
            digitalocean_database_cluster_node_size,
        ) = get_cluster_data(
            digitalocean_k8s_cluster_region,
            digitalocean_database_cluster_region,
            digitalocean_database_cluster_node_size,
        )
    if sentry_org:
        sentry_url = get_sentry_url(sentry_url)
        sentry_auth_token = get_sentry_token(sentry_auth_token)
    if use_pact is None:
        use_pact = get_use_pact()
    if use_pact:
        pact_broker_url, pact_broker_username, pact_broker_password = get_broker_data(
            use_pact, pact_broker_url, pact_broker_username, pact_broker_password
        )
    if media_storage is None:
        media_storage = get_media_storage()
    if use_gitlab is None:
        use_gitlab = get_use_gitlab(use_gitlab)
    if use_gitlab:
        (
            gitlab_group_slug,
            gitlab_private_token,
            gitlab_group_owners,
            gitlab_group_maintainers,
            gitlab_group_developers,
        ) = get_gitlab_group_data(
            media_storage,
            gitlab_group_slug,
            gitlab_private_token,
            gitlab_group_owners,
            gitlab_group_maintainers,
            gitlab_group_developers,
        )
        if media_storage == "s3-digitalocean":
            (
                digitalocean_token,
                digitalocean_spaces_bucket_region,
                digitalocean_spaces_access_id,
                digitalocean_spaces_secret_key,
            ) = get_digitalocean_media_storage_data()
    run(
        uid,
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
        environment_distribution,
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
