terraform {
  required_providers {
    vault = {
      source  = "hashicorp/vault"
      version = "3.7.0"
    }
  }
}

provider "vault" {
}

/* GitLab JWT Auth */

resource "vault_jwt_auth_backend" "gitlab_jwt" {
  description  = "Demonstration of the Terraform JWT auth backend"
  path         = "gitlab-jwt-${var.project_path}"
  jwks_url     = format("%s/-/jwks", trimsuffix(var.gitlab_url, "/"))
  bound_issuer = var.gitlab_url
}

resource "vault_policy" "gitlab_jwt_stacks" {
  for_each = var.stacks_environments

  name = "gitlab-jwt-${var.project_path}-stacks-${each.key}"

  policy = <<EOF
# Read-only permission for GitLab CI jobs on project "${var.project_name}" ${each.key} stack secrets

path "${var.project_path}/stacks/${each.key}/*" {
  capabilities = [ "read" ]
}

path "${var.project_path}-tfc/creds/default" {
  capabilities = [ "read" ]
}
EOF
}

resource "vault_jwt_auth_backend_role" "gitlab_jwt_stacks" {
  for_each = vault_policy.gitlab_jwt_stacks

  backend = vault_jwt_auth_backend.gitlab_jwt.path

  role_name = each.value.name
  role_type = "jwt"

  token_explicit_max_ttl = var.gitlab_jwt_auth_token_explicit_max_ttl
  token_policies         = [each.value.name]

  user_claim = "user_email"

  bound_claims      = { namespace_path = var.project_path }
}

resource "vault_policy" "gitlab_jwt_envs" {
  for_each = transpose({ for k, v in var.stacks_environments : k => keys(v) })

  name = "gitlab-jwt-${var.project_path}-envs-${each.key}"

  policy = <<EOF
# Read-only permission for GitLab CI jobs on project "${var.project_name}" ${each.key} stack secrets

path "${var.project_path}/stacks/${each.value[0]}/*" {
  capabilities = [ "read" ]
}

path "${var.project_path}/envs/${each.key}/*" {
  capabilities = [ "read" ]
}

path "${var.project_path}-tfc/creds/default" {
  capabilities = [ "read" ]
}
EOF
}

resource "vault_jwt_auth_backend_role" "envs" {
  for_each = vault_policy.gitlab_jwt_envs

  backend = vault_jwt_auth_backend.gitlab_jwt.path

  role_name = each.value.name
  role_type = "jwt"

  token_explicit_max_ttl = var.gitlab_jwt_auth_token_explicit_max_ttl
  token_policies         = [each.value.name]

  user_claim = "user_email"

  bound_claims      = { namespace_path = var.project_path }
}

/* GitLab OIDC Auth */

data "vault_auth_backend" "gitlab_oidc" {
  count = var.gitlab_oidc_auth_path != "" ? 1 : 0

  path = var.gitlab_oidc_auth_path
}

resource "vault_policy" "gitlab_oidc" {
  count = var.gitlab_oidc_auth_path != "" ? 1 : 0

  name = "gitlab-oidc-${var.project_path}"

  policy = <<EOF
# Full permission for GitLab group members on project "${var.project_name}" secrets

path "sys/mounts" {
  capabilities = [ "read" ]
}

# Manage KV secrets
path "sys/mounts/${var.project_path}" {
  capabilities = [ "create", "delete", "update" ]
}

path "${var.project_path}" {                                                                                                                                                 
  capabilities = [ "list" ]                                                                                                                                  
}

path "${var.project_path}/*" {                                                                                                                                                 
  capabilities = [ "create", "delete", "list", "read", "update" ]                                                                                                                                  
}

# Manage TFC secrets
path "sys/mounts/${var.project_path}-tfc" {
  capabilities = [ "create", "delete", "update" ]
}

path "${var.project_path}-tfc" {                                                                                                                                                 
  capabilities = [ "list" ]                                                                                                                             
}

path "${var.project_path}-tfc/*" {                                                                                                                                                 
  capabilities = [ "create", "delete", "list", "read", "update" ]                                                                                                                                 
}

# Enable child token generation for the Terraform Vault provider
# https://registry.terraform.io/providers/hashicorp/vault/latest/docs#token
path "auth/token/create" {                                                                                                                                                 
  capabilities = [ "update" ]                                                                                                                                  
}
EOF
}

resource "vault_identity_group" "gitlab_oidc" {
  count = var.gitlab_oidc_auth_path != "" ? 1 : 0

  name     = "gitlab-oidc-${var.project_path}"
  type     = "external"
  policies = [vault_policy.gitlab_oidc[0].name]
}

resource "vault_identity_group_alias" "gitlab_oidc" {
  count = var.gitlab_oidc_auth_path != "" ? 1 : 0

  name           = "gitlab-oidc-${var.project_path}"
  mount_accessor = data.vault_auth_backend.gitlab_oidc[0].accessor
  canonical_id   = vault_identity_group.gitlab_oidc[0].id
}
