#!/bin/sh -e

curl https://releases.hashicorp.com/vault/${VAULT_VERSION:=1.11.0}/vault_${VAULT_VERSION}_linux_386.zip --output vault.zip
unzip vault.zip

export VAULT_TOKEN="$(./vault write -field=token auth/gitlab-jwt/login role=${VAULT_ROLE} jwt=${CI_JOB_JWT_V2})"

for secret_path in ${VAULT_SECRETS}
do
    secret_var_file=${TERRAFORM_VARS_DIR}/`echo ${secret_path} | tr / -`.json
    (./vault kv get -format='json' -field=data ${PROJECT_SLUG}/${VAULT_SECRETS_PREFIX}/${secret_path} 2> /dev/null || echo {}) > ${secret_var_file}
    var_files="${var_files} -var-file=${secret_var_file}"
done

if [ "${TERRAFORM_BACKEND}" == "terraform-cloud" ]; then
    export TFC_TOKEN="$(./vault read -field=token ${PROJECT_SLUG}-tfc/creds/default)"
fi
