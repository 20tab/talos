#!/bin/sh -e

export TF_CLI_CONFIG_FILE="${TF_ROOT}/cloud.tfc"
cat << EOF > "${TF_CLI_CONFIG_FILE}"
{
  "credentials": {
    "app.terraform.io": {
      "token": "${TFC_TOKEN}"
    }
  }
}
EOF
