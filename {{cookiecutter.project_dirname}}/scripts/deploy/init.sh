#!/usr/bin/env sh

set -e

export TF_VAR_env_slug="${ENV_SLUG}"
export TF_VAR_project_slug="${PROJECT_SLUG}"
export TF_VAR_stack_slug="${STACK_SLUG}"

terraform_cli_args="-var-file=${TERRAFORM_VARS_DIR%/}/.tfvars"

if [ "${TERRAFORM_EXTRA_VAR_FILE}" != "" ]; then
  extra_var_file="${TERRAFORM_VARS_DIR%/}/${TERRAFORM_EXTRA_VAR_FILE}"
  touch "${extra_var_file}"
  terraform_cli_args="${terraform_cli_args} -var-file=${extra_var_file}"
fi

if [ "${VAULT_ADDR}" != "" ]; then
  . "${PROJECT_DIR}"/scripts/deploy/vault.sh
  terraform_cli_args="${terraform_cli_args} -var-file=${TERRAFORM_VARS_DIR%/}/vault-secrets.tfvars.json"
fi

export TF_CLI_ARGS_destroy="${terraform_cli_args}"
export TF_CLI_ARGS_plan="${terraform_cli_args}"

case "${TERRAFORM_BACKEND}" in
  "gitlab")
    . "${PROJECT_DIR}"/scripts/deploy/gitlab.sh
  ;;
  "terraform-cloud")
    . "${PROJECT_DIR}"/scripts/deploy/terraform-cloud.sh
  ;;
esac
