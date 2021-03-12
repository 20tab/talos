#!/usr/bin/env bash

# Bash "strict mode", to help catch problems and bugs in the shell script
# http://redsymbol.net/articles/unofficial-bash-strict-mode/
# set -euo pipefail

kubectl apply -f k8s/cluster/gitlab-admin-service-account.yaml
python3 ./scripts/python/add_cluster.py
