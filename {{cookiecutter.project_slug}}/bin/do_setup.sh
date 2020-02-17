#!/bin/bash

helpFunction()
{
   echo ""
   echo "Usage: $0 -a do_access_token -c cluster_name -r region"
   echo -e "\t-a Access token generated on DigitalOcean API site"
   echo -e "\t-c Created cluster's name"
   echo -e "\t-r Region used during cluster creation"
   exit 1 # Exit script after printing help
}

while getopts "a:c:r:" opt
do
   case "$opt" in
      a ) parameterA="$OPTARG" ;;
      c ) parameterC="$OPTARG" ;;
      r ) parameterR="$OPTARG" ;;
      ? ) helpFunction ;; # Print helpFunction in case parameter is non-existent
   esac
done

# Print helpFunction in case parameters are empty
if [ -z "$parameterA" ] || [ -z "$parameterC" ] || [ -z "$parameterR" ]
then
   echo "Some or all of the parameters are empty";
   helpFunction
fi

doctl auth init -t $parameterA
doctl kubernetes cluster kubeconfig save $parameterC
kubectl config use-context $parameterR-$parameterC
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/nginx-0.28.0/deploy/static/mandatory.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/nginx-0.28.0/deploy/static/provider/cloud-generic.yaml
kubectl create secret docker-registry regcred --docker-server=http://registry.gitlab.com --docker-username=DO_GITLAB_USERNAME --docker-password=DO_GITLAB_PASSWORD --docker-email=DO_GITLAB_EMAIL
