#!/bin/bash

helpFunction()
{
   echo ""
   echo "Usage: $0 -c cluster_name -r region"
   echo -e "\t-c Created cluster's name"
   echo -e "\t-r Region used during cluster creation"
   exit 1 # Exit script after printing help
}

while getopts "a:c:r:" opt
do
   case "$opt" in
      c ) parameterC="$OPTARG" ;;
      r ) parameterR="$OPTARG" ;;
      ? ) helpFunction ;; # Print helpFunction in case parameter is non-existent
   esac
done

# Print helpFunction in case parameters are empty
if [ -z "$parameterC" ] || [ -z "$parameterR" ]
then
   echo "Some required parameters are empty";
   helpFunction
fi

doctl auth init
doctl kubernetes cluster kubeconfig save $parameterC
kubectl config use-context $parameterR-$parameterC
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/nginx-0.28.0/deploy/static/mandatory.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/nginx-0.28.0/deploy/static/provider/cloud-generic.yaml
