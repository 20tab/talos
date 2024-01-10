#!/usr/bin/env sh

set -e

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
