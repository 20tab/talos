#!/usr/bin/env bash

RELEASE_VERSION="release-2.3"

kubectl apply -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/$RELEASE_VERSION/examples/standard/cluster-role-binding.yaml \
-f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/$RELEASE_VERSION/examples/standard/cluster-role.yaml \
-f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/$RELEASE_VERSION/examples/standard/deployment.yaml \
-f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/$RELEASE_VERSION/examples/standard/service-account.yaml \
-f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/$RELEASE_VERSION/examples/standard/service.yaml
