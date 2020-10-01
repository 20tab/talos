#!/bin/bash

doctl auth init
python3 ./scripts/python/do_setup.py
kubectl apply -f kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v0.35.0/deploy/static/provider/do/deploy.yaml

while true; do
   read -p "Do you want to add cluster to gitlab group?[Y/n]: "  yn
   case $yn in
      [Yy]* ) ./scripts/add_cluster.sh;exit;;
      [Nn]* ) exit;;
      * ) echo "Please answer yes or no.";;
   esac
done
