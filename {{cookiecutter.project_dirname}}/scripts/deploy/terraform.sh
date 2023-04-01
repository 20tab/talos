#!/usr/bin/env sh

set -e

if [ "${DEBUG_OUTPUT}" = "true" ]; then
    set -ex
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

# Use terraform automation mode (will remove some verbose unneeded messages)
export TF_IN_AUTOMATION=true

init() {
  cd "${TF_ROOT}"
  if [ "${TERRAFORM_BACKEND}" = "terraform-cloud" ]; then
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
    terraform "${@}" -auto-approve
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
    terraform "${@}" -input=false -out="${plan_cache}"
  ;;
  "plan-json")
    init
    terraform plan -input=false -out="${plan_cache}"
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
