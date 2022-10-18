#!/bin/sh -e

curl https://releases.hashicorp.com/vault/${VAULT_VERSION:=1.11.0}/vault_${VAULT_VERSION}_linux_386.zip --output vault.zip
unzip vault.zip

load_secrets()
{
    secrets_prefix=$1
    secrets_slug=$2
    export VAULT_TOKEN="$(./vault write -field=token auth/gitlab-jwt-${PROJECT_SLUG}/login role=${secrets_prefix}-${secrets_slug} jwt=${CI_JOB_JWT_V2})"
    for secret_name in $3
    do
        secret_var_file=${TERRAFORM_VARS_DIR}/${secret_name}.json
        (./vault kv get -format='json' -field=data ${PROJECT_SLUG}/${secrets_prefix}/${secrets_slug}/${secret_name} 2> /dev/null || echo {}) > ${secret_var_file}
        var_files="${var_files} -var-file=${secret_var_file}"
    done
}

if [ "${STACK_SLUG}" != "" ] && [ "${VAULT_STACK_SECRETS}" != "" ]; then
    load_secrets "stacks" ${STACK_SLUG} "${VAULT_STACK_SECRETS}"
fi

if [ "${ENV_SLUG}" != "" ] && [ "${VAULT_ENV_SECRETS}" != "" ]; then
    load_secrets "envs" ${ENV_SLUG} "${VAULT_ENV_SECRETS}"
fi

if [ "${TERRAFORM_BACKEND}" == "terraform-cloud" ]; then
    export TFC_TOKEN="$(./vault read -field=token ${PROJECT_SLUG}-tfc/creds/default)"
fi
