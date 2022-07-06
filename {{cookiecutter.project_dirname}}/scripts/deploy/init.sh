#!/bin/sh -e

export TF_VAR_env_slug="${ENV_SLUG}"
export TF_VAR_project_slug="${PROJECT_SLUG}"
export TF_VAR_stack_slug="${STACK_SLUG}"

var_file="${TERRAFORM_VARS_DIR}/.tfvars"

if [ "${TERRAFORM_EXTRA_VAR_FILE}" != "" ]; then
  extra_var_file="${TERRAFORM_VARS_DIR}/${TERRAFORM_EXTRA_VAR_FILE}"
  touch ${extra_var_file}
  var_files="-var-file=${var_file} -var-file=${extra_var_file}"
else
  var_files="-var-file=${var_file}"
fi

if [ "${VAULT_ADDR}" != "" ]; then
  . ${PROJECT_DIR}/scripts/deploy/vault.sh
fi

export TERRAFORM_VAR_FILE_ARGS=${var_files}

case "${TERRAFORM_BACKEND}" in
  "gitlab")
    . ${PROJECT_DIR}/scripts/deploy/gitlab.sh
  ;;
  "terraform-cloud")
    . ${PROJECT_DIR}/scripts/deploy/terraform-cloud.sh
  ;;
esac
