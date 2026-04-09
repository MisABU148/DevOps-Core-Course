#!/bin/sh

vault auth enable kubernetes

vault secrets enable -path=secret kv-v2

vault kv put secret/app username=admin password=supersecret

vault policy write app-policy policy.hcl

vault write auth/kubernetes/role/app-role \
  bound_service_account_names=default \
  bound_service_account_namespaces=default \
  policies=app-policy \
  ttl=1h