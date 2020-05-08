#!/bin/bash


doctl auth init
python3 ./scripts/python/do_setup.py
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/nginx-0.30.0/deploy/static/mandatory.yaml
kubectl apply -f ./k8s/cluster/ingress-nginx-20tab.yaml

while true; do
   read -p "Do you want to add cluster to gitlab group?[Y/n]: "  yn
   case $yn in
      [Yy]* ) ./scripts/add_cluster.sh;exit;;
      [Nn]* ) exit;;
      * ) echo "Please answer yes or no.";;
   esac
done
