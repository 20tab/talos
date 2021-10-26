#!/usr/bin/env python
"""Initialize a web project Django service based on a template."""

import os
import re
import secrets
import shutil
import subprocess
from functools import partial
from pathlib import Path

import click
import validators
from cookiecutter.main import cookiecutter
from slugify import slugify

BACKEND_TEMPLATE_URLS = {
    "django": "https://github.com/20tab/django-continuous-delivery"
}
BACKEND_TYPE_CHOICES = ["django", "none"]
DEFAULT_SERVICE_SLUG = "orchestrator"
DEPLOY_TYPE_CHOICES = ["k8s-digitalocean", "k8s-other"]
DEPLOY_TYPE_DEFAULT = "k8s-digitalocean"
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


def init_service(
    output_dir,
    project_name,
    project_slug,
    project_dirname,
    backend_type,
    frontend_type,
    media_storage,
):
    """Initialize the service."""
    click.echo(info("...cookiecutting the service"))
    cookiecutter(
        ".",
        extra_context={
            "backend_type": backend_type,
            "frontend_type": frontend_type,
            "media_storage": media_storage,
            "project_dirname": project_dirname,
            "project_name": project_name,
            "project_slug": project_slug,
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
    env_path.write_text(env_text)


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
):
    """Initialize the Gitlab repositories."""
    click.echo(info("...creating the Gitlab repository and associated resources"))
    env = {
        "TF_VAR_gitlab_group_variables": "{%s}"
        % ", ".join(f"{k} = {v}" for k, v in gitlab_group_variables.items()),
        "TF_VAR_gitlab_group_slug": gitlab_group_slug,
        "TF_VAR_gitlab_token": gitlab_private_token,
        "TF_VAR_gitlab_group_developers": gitlab_group_developers,
        "TF_VAR_gitlab_group_maintainers": gitlab_group_maintainers,
        "TF_VAR_gitlab_group_owners": gitlab_group_owners,
        "TF_VAR_project_name": project_name,
        "TF_VAR_project_slug": project_slug,
        "TF_VAR_gitlab_project_variables": "{%s}"
        % ", ".join(f"{k} = {v}" for k, v in gitlab_project_variables.items()),
        "TF_VAR_service_dir": service_dir,
        "TF_VAR_service_slug": service_slug,
    }
    cwd = Path("terraform")
    init_process = subprocess.run(
        ["terraform", "init", "-reconfigure", "-input=false", "-no-color"],
        capture_output=True,
        cwd=cwd,
        env=env,
        text=True,
    )
    if init_process.returncode == 0:
        (cwd / ".terraform-init.log").write_text(init_process.stdout)
        apply_process = subprocess.run(
            ["terraform", "apply", "-auto-approve", "-input=false", "-no-color"],
            capture_output=True,
            cwd=cwd,
            env=env,
            text=True,
        )
        if apply_process.returncode == 0:
            (cwd / ".terraform-apply.log").write_text(apply_process.stdout)
        else:
            (cwd / ".terraform-apply-errors.log").write_text(apply_process.stderr)
            click.echo(
                error(
                    "Error applying Terraform Gitlab configuration "
                    "(see terraform/.terraform-apply-errors.log)"
                )
            )
            raise click.Abort()
    else:
        (cwd / ".terraform-init-errors.log").write_text(init_process.stderr)
        click.echo(
            error(
                "Error initializing Terraform "
                "(see terraform/.terraform-init-errors.log)"
            )
        )
        raise click.Abort()


def change_output_owner(service_dir, uid):
    """Change the owner of the output directory recursively."""
    uid is not None and subprocess.run(["chown", "-R", uid, service_dir])


def init_subrepo(service_slug, service_dir, template_url, **options):
    """Initialize a subrepo using the given template and options."""
    subrepo_dir = str(Path(SUBREPOS_DIR) / service_slug)
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
        service_dir=str(Path(service_dir) / service_slug),
    )
    subprocess.run(
        ["python", "-c", f"from bootstrap import run; run(**{options})"],
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
    frontend_type,
    project_url_dev,
    project_url_stage,
    project_url_prod,
    deploy_type,
    digitalocean_token,
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
):
    """Run the bootstrap."""
    click.echo(highlight(f"Initializing the {service_slug} service:"))
    init_service(
        output_dir,
        project_name,
        project_slug,
        project_dirname,
        backend_type,
        frontend_type,
        media_storage,
    )
    create_env_file(service_dir)
    if use_gitlab:
        gitlab_project_variables = {}
        gitlab_group_variables = {}
        if sentry_org:
            gitlab_group_variables.update(
                SENTRY_ORG='{value = "%s", masked = false}' % sentry_org,
                SENTRY_URL='{value = "%s", masked = false}' % sentry_url,
                SENTRY_AUTH_TOKEN='{value = "%s"}' % sentry_auth_token,
            )
        if use_pact:
            pact_broker_auth_url = re.sub(
                r"^(https?)://(.*)$",
                fr"\g<1>://{pact_broker_username}:{pact_broker_password}@\g<2>",
                pact_broker_url,
            )
            gitlab_group_variables.update(
                PACT_ENABLED='{value = "true", protected = false, masked = false}',
                PACT_BROKER_BASE_URL=(
                    '{value = "%s", protected = false, masked = false}'
                    % pact_broker_url
                ),
                PACT_BROKER_USERNAME=(
                    '{value = "%s", protected = false, masked = false}'
                    % pact_broker_username
                ),
                PACT_BROKER_PASSWORD=(
                    '{value = "%s", protected = false}' % pact_broker_password
                ),
                PACT_BROKER_AUTH_URL=('{value = "%s"}' % pact_broker_auth_url),
            )
        if media_storage == "s3-digitalocean":
            gitlab_group_variables.update(
                DIGITALOCEAN_BUCKET_REGION=(
                    '{value = "%s", masked = false}' % digitalocean_spaces_bucket_region
                ),
                DIGITALOCEAN_SPACES_ACCESS_ID=(
                    '{value = "%s"}' % digitalocean_spaces_access_id
                ),
                DIGITALOCEAN_SPACES_SECRET_KEY=(
                    '{value = "%s"}' % digitalocean_spaces_secret_key
                ),
            )
        digitalocean_token and gitlab_group_variables.update(
            DIGITALOCEAN_TOKEN='{value = "%s"}' % digitalocean_token
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
        )
    common_options = {
        "uid": uid,
        "output_dir": service_dir,
        "project_name": project_name,
        "project_slug": project_slug,
        "project_url_dev": project_url_dev,
        "project_url_stage": project_url_stage,
        "project_url_prod": project_url_prod,
        "deploy_type": deploy_type,
        "digitalocean_token": digitalocean_token,
        "use_gitlab": use_gitlab,
        "create_group_variables": False,
        "gitlab_private_token": gitlab_private_token,
        "gitlab_group_slug": gitlab_group_slug,
    }
    backend_template_url = BACKEND_TEMPLATE_URLS.get(backend_type)
    if backend_template_url:
        init_subrepo(
            backend_type,
            service_dir,
            backend_template_url,
            media_storage=media_storage,
            digitalocean_spaces_bucket_region=digitalocean_spaces_bucket_region,
            digitalocean_spaces_access_id=digitalocean_spaces_access_id,
            digitalocean_spaces_secret_key=digitalocean_spaces_secret_key,
            **common_options,
        )
    frontend_template_url = FRONTEND_TEMPLATE_URLS.get(frontend_type)
    if frontend_template_url:
        init_subrepo(
            frontend_type,
            service_dir,
            frontend_template_url,
            **common_options,
        )
    change_output_owner(service_dir, uid)


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
@click.option("--output-dir", default=".", required=OUTPUT_DIR is None)
@click.option("--project-name", prompt=True)
@click.option("--project-slug", callback=slugify_option)
@click.option("--project-dirname")
@click.option("--backend-type")
@click.option("--frontend-type")
@click.option("--project-url-dev")
@click.option("--project-url-stage")
@click.option("--project-url-prod")
@click.option(
    "--deploy-type",
    type=click.Choice(DEPLOY_TYPE_CHOICES, case_sensitive=False),
)
@click.option("--digitalocean-token")
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
@click.option("--use-gitlab/--no-gitlab", is_flag=True, default=None)
@click.option("--gitlab-private-token", envvar=GITLAB_TOKEN_ENV_VAR)
@click.option("--gitlab-group-slug")
@click.option("--gitlab-group-owners", default="")
@click.option("--gitlab-group-maintainers", default="")
@click.option("--gitlab-group-developers", default="")
def init_command(
    uid,
    output_dir,
    project_name,
    project_slug,
    project_dirname,
    backend_type,
    frontend_type,
    project_url_dev,
    project_url_stage,
    project_url_prod,
    deploy_type,
    digitalocean_token,
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
):
    """Collect options and run the bootstrap."""
    output_dir = OUTPUT_DIR or output_dir
    project_slug = slugify(
        project_slug or click.prompt("Project slug", default=slugify(project_name)),
    )
    project_dirname = slugify(project_slug, separator="")
    service_slug = DEFAULT_SERVICE_SLUG
    service_dir = str(Path(output_dir) / project_dirname)
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
    frontend_type = (
        frontend_type in FRONTEND_TYPE_CHOICES
        and frontend_type
        or click.prompt(
            "Frontend type",
            default=FRONTEND_TYPE_CHOICES[0],
            type=click.Choice(FRONTEND_TYPE_CHOICES, case_sensitive=False),
        )
    ).lower()
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
    deploy_type = (
        deploy_type in DEPLOY_TYPE_CHOICES
        and deploy_type
        or click.prompt(
            "Deploy type",
            default=DEPLOY_TYPE_DEFAULT,
            type=click.Choice(DEPLOY_TYPE_CHOICES, case_sensitive=False),
        )
    ).lower()
    if "digitalocean" in deploy_type:
        digitalocean_token = validate_or_prompt_password(
            digitalocean_token,
            "DigitalOcean token",
            required=True,
        )
    sentry_org = sentry_org or click.prompt(
        'Sentry organization (e.g. "20tab", leave blank if unused)',
        default="",
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
        output_dir,
        project_name,
        project_slug,
        project_dirname,
        service_slug,
        service_dir,
        backend_type,
        frontend_type,
        project_url_dev,
        project_url_stage,
        project_url_prod,
        deploy_type,
        digitalocean_token,
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
    )


if __name__ == "__main__":
    init_command()
