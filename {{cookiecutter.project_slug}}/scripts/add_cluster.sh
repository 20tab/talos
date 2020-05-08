#!/bin/bash

kubectl apply -f k8s/cluster/gitlab-admin-service-account.yaml
kubectl -n kube-system describe secret $(kubectl -n kube-system get secret | grep gitlab-admin | awk '{print $1}') > do_token.yaml
python3 ./scripts/python/add_cluster.py
