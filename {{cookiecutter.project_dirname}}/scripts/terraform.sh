#!/bin/sh -e

if [ "${DEBUG_OUTPUT}" == "true" ]; then
    set -x
fi

plan_cache="plan.cache"
plan_json="plan.json"

JQ_PLAN='
  (
    [.resource_changes[]?.change.actions?] | flatten
  ) | {
    "create":(map(select(.=="create")) | length),
    "update":(map(select(.=="update")) | length),
    "delete":(map(select(.=="delete")) | length)
  }
'

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
  TERRAFORM_SECRETS_VAR_FILE=${TERRAFORM_VARS_DIR}/secrets.json
  . ${PROJECT_DIR}/scripts/vault.sh
  var_files="${var_files} -var-file=${TERRAFORM_SECRETS_VAR_FILE}"
fi

case "${TERRAFORM_BACKEND}" in
  "gitlab")
    . ${PROJECT_DIR}/scripts/gitlab.sh
  ;;
  "terraform-cloud")
    . ${PROJECT_DIR}/scripts/terraform-cloud.sh
  ;;
esac

# Use terraform automation mode (will remove some verbose unneeded messages)
export TF_IN_AUTOMATION=true

init() {
  cd ${TF_ROOT}
  if [ "${TERRAFORM_BACKEND}" == "terraform-cloud" ]; then
    terraform init "${@}" -input=false
  else
    terraform init "${@}" -input=false -reconfigure
  fi
}

case "${1}" in
  "apply")
    init
    terraform "${@}" -input=false "${plan_cache}"
  ;;
  "destroy")
    init
    terraform "${@}" ${var_files} -auto-approve
  ;;
  "fmt")
    terraform "${@}" -check -diff -recursive
  ;;
  "init")
    # shift argument list „one to the left“ to not call 'terraform init init'
    shift
    init "${@}"
  ;;
  "plan")
    init
    terraform "${@}" ${var_files} -input=false -out="${plan_cache}"
  ;;
  "plan-json")
    init
    terraform plan ${var_files} -input=false -out="${plan_cache}"
    terraform show -json "${plan_cache}" | \
      jq -r "${JQ_PLAN}" \
      > "${plan_json}"
  ;;
  "validate")
    init -backend=false
    terraform "${@}"
  ;;
  *)
    terraform "${@}"
  ;;
esac
