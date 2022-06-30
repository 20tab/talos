#!/bin/sh -e

if [ "${DEBUG_OUTPUT}" == "true" ]; then
    set -x
fi

export TF_VAR_env_slug="${ENV_SLUG}"
export TF_VAR_project_slug="${PROJECT_SLUG}"
export TF_VAR_stack_slug="${STACK_SLUG}"

plan_cache="plan.cache"
plan_json="plan.json"
var_file="${TERRAFORM_VARS_DIR}/.tfvars"

JQ_PLAN='
  (
    [.resource_changes[]?.change.actions?] | flatten
  ) | {
    "create":(map(select(.=="create")) | length),
    "update":(map(select(.=="update")) | length),
    "delete":(map(select(.=="delete")) | length)
  }
'

if [ "${VAULT_ADDR}" != "" ]; then
  curl https://releases.hashicorp.com/vault/${VAULT_VERSION:=1.11.0}/vault_${VAULT_VERSION}_linux_386.zip --output vault.zip
  unzip vault.zip
  export VAULT_TOKEN="$(./vault write -field=token auth/gitlab-jwt/login role=${PROJECT_SLUG} jwt=${CI_JOB_JWT_V2})"
  if [ "${TERRAFORM_BACKEND}" == "terraform-cloud" ]; then
    export TFC_TOKEN="$(./vault read -field=token ${PROJECT_SLUG}-tfc/creds/default)"
  fi
fi

case "${TERRAFORM_BACKEND}" in
  "gitlab")
    # If TF_USERNAME is unset then default to GITLAB_USER_LOGIN
    TF_USERNAME="${TF_USERNAME:-${GITLAB_USER_LOGIN}}"
    # If TF_PASSWORD is unset then default to gitlab-ci-token/CI_JOB_TOKEN
    if [ -z "${TF_PASSWORD}" ]; then
    TF_USERNAME="gitlab-ci-token"
    TF_PASSWORD="${CI_JOB_TOKEN}"
    fi
    # If TF_ADDRESS is unset but TF_STATE_NAME is provided, then default to GitLab backend in current project
    if [ -n "${TF_STATE_NAME}" ]; then
    TF_ADDRESS="${TF_ADDRESS:-${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/terraform/state/${TF_STATE_NAME}}"
    fi
    # Set variables for the HTTP backend to default to TF_* values
    export TF_HTTP_ADDRESS="${TF_HTTP_ADDRESS:-${TF_ADDRESS}}"
    export TF_HTTP_LOCK_ADDRESS="${TF_HTTP_LOCK_ADDRESS:-${TF_ADDRESS}/lock}"
    export TF_HTTP_LOCK_METHOD="${TF_HTTP_LOCK_METHOD:-POST}"
    export TF_HTTP_UNLOCK_ADDRESS="${TF_HTTP_UNLOCK_ADDRESS:-${TF_ADDRESS}/lock}"
    export TF_HTTP_UNLOCK_METHOD="${TF_HTTP_UNLOCK_METHOD:-DELETE}"
    export TF_HTTP_USERNAME="${TF_HTTP_USERNAME:-${TF_USERNAME}}"
    export TF_HTTP_PASSWORD="${TF_HTTP_PASSWORD:-${TF_PASSWORD}}"
    export TF_HTTP_RETRY_WAIT_MIN="${TF_HTTP_RETRY_WAIT_MIN:-5}"
    # Expose Gitlab specific variables to terraform since no -tf-var is available
    # Usable in the .tf file as variable "CI_JOB_ID" { type = string } etc
    export TF_VAR_CI_JOB_ID="${TF_VAR_CI_JOB_ID:-${CI_JOB_ID}}"
    export TF_VAR_CI_COMMIT_SHA="${TF_VAR_CI_COMMIT_SHA:-${CI_COMMIT_SHA}}"
    export TF_VAR_CI_JOB_STAGE="${TF_VAR_CI_JOB_STAGE:-${CI_JOB_STAGE}}"
    export TF_VAR_CI_PROJECT_ID="${TF_VAR_CI_PROJECT_ID:-${CI_PROJECT_ID}}"
    export TF_VAR_CI_PROJECT_NAME="${TF_VAR_CI_PROJECT_NAME:-${CI_PROJECT_NAME}}"
    export TF_VAR_CI_PROJECT_NAMESPACE="${TF_VAR_CI_PROJECT_NAMESPACE:-${CI_PROJECT_NAMESPACE}}"
    export TF_VAR_CI_PROJECT_PATH="${TF_VAR_CI_PROJECT_PATH:-${CI_PROJECT_PATH}}"
    export TF_VAR_CI_PROJECT_URL="${TF_VAR_CI_PROJECT_URL:-${CI_PROJECT_URL}}"
  ;;
  "terraform-cloud")
    export TF_CLI_CONFIG_FILE="${TF_ROOT}/cloud.tfc"
    cat << EOF > ${TF_CLI_CONFIG_FILE}
{
  "credentials": {
    "app.terraform.io": {
      "token": "${TFC_TOKEN}"
    }
  }
}
EOF
  ;;
esac

if [ "${TERRAFORM_EXTRA_VAR_FILE}" != "" ]; then
  extra_var_file="${TERRAFORM_VARS_DIR}/${TERRAFORM_EXTRA_VAR_FILE}"
  touch ${extra_var_file}
  var_files="-var-file=${var_file} -var-file=${extra_var_file}"
else
  var_files="-var-file=${var_file}"
fi

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
