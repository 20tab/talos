#!/bin/sh -e

curl https://releases.hashicorp.com/vault/${VAULT_VERSION:=1.11.0}/vault_${VAULT_VERSION}_linux_386.zip --output vault.zip
unzip vault.zip

export VAULT_TOKEN="$(./vault write -field=token auth/gitlab-jwt/login role=${PROJECT_SLUG} jwt=${CI_JOB_JWT_V2})"

(./vault kv get -format='json' -field=data ${VAULT_SECRET_NAME} 2> /dev/null || echo {}) > ${TERRAFORM_SECRETS_VAR_FILE}

if [ "${TERRAFORM_BACKEND}" == "terraform-cloud" ]; then
    export TFC_TOKEN="$(./vault read -field=token ${PROJECT_SLUG}-tfc/creds/default)"
fi
