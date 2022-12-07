#!/bin/sh -e

export VAULT_TOKEN=`curl --silent --request POST --data "role=${VAULT_ROLE}" --data "jwt=${CI_JOB_JWT_V2}" ${VAULT_ADDR%/}/v1/auth/gitlab-jwt/login | jq -r .auth.client_token`

for secret_path in ${VAULT_SECRETS}
do
    secret_var_file=${TERRAFORM_VARS_DIR}/`echo ${secret_path} | tr / -`.json
    curl --silent --header "X-Vault-Token: ${VAULT_TOKEN}" ${VAULT_ADDR%/}/v1/${PROJECT_SLUG}/${VAULT_SECRETS_PREFIX}/${secret_path} | jq -r ".data // {}" > ${secret_var_file}
    var_files="${var_files} -var-file=${secret_var_file}"
done

if [ "${TERRAFORM_BACKEND}" == "terraform-cloud" ]; then
    export TFC_TOKEN=`curl --silent --header "X-Vault-Token: ${VAULT_TOKEN}" ${VAULT_ADDR%/}/v1/${PROJECT_SLUG}-tfc/creds/default | jq -r .data.token `
fi
