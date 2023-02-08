#!/bin/sh -e

vault_token=$(curl --silent --request POST --data "role=${VAULT_ROLE}" --data "jwt=${CI_JOB_JWT_V2}" "${VAULT_ADDR%/}"/v1/auth/gitlab-jwt/login | jq -r .auth.client_token)

secrets_data="{}"

for secret_path in ${VAULT_SECRETS}
do
    secret_data=$(curl --silent --header "X-Vault-Token: ${vault_token}" "${VAULT_ADDR%/}"/v1/"${PROJECT_SLUG}"/"${VAULT_SECRETS_PREFIX}"/"${secret_path}" | jq -r '.data // {}') || secret_data="{}"
    secrets_data=$(echo "${secrets_data}" | jq --argjson new_data "${secret_data}" '. * $new_data')
done

echo "${secrets_data}" > "${TERRAFORM_VARS_DIR%/}"/vault-secrets.tfvars.json

if [ "${TERRAFORM_BACKEND}" = "terraform-cloud" ]; then
    TFC_TOKEN=$(curl --silent --header "X-Vault-Token: ${vault_token}" "${VAULT_ADDR%/}"/v1/"${PROJECT_SLUG}"-tfc/creds/default | jq -r .data.token)
    export TFC_TOKEN
fi
