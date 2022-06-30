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

data "vault_auth_backend" "gitlab_jwt" {
  count = var.gitlab_jwt_auth_path != "" ? 1 : 0

  path = var.gitlab_jwt_auth_path
}

resource "vault_policy" "gitlab_jwt_read" {
  count = var.gitlab_jwt_auth_path != "" ? 1 : 0

  name = "gitlab-jwt-${var.project_path}-read"

  policy = <<EOF
# Read-only permission for GitLab CI jobs on project "${var.project_name}" secrets

path "{{identity.entity.aliases.${data.vault_auth_backend.gitlab_jwt[0].accessor}.metadata.project_path}}/*" {
  capabilities = [ "read" ]
}

path "{{identity.entity.aliases.${data.vault_auth_backend.gitlab_jwt[0].accessor}.metadata.project_slug}}/ci-jobs" {
  capabilities = [ "read" ]
}

path "{{identity.entity.aliases.${data.vault_auth_backend.gitlab_jwt[0].accessor}.metadata.project_slug}}-tfc/creds/default" {
  capabilities = [ "read" ]
}
EOF
}

resource "vault_jwt_auth_backend_role" "main" {
  count = var.gitlab_jwt_auth_path != "" ? 1 : 0

  backend = data.vault_auth_backend.gitlab_jwt[0].path

  role_name = var.project_path
  role_type = "jwt"

  token_explicit_max_ttl = var.gitlab_jwt_auth_token_explicit_max_ttl
  token_policies         = [vault_policy.gitlab_jwt_read[0].name]

  user_claim = "user_email"

  bound_claims_type = "glob"
  bound_claims      = { namespace_path = var.project_path }
  claim_mappings = {
    namespace_path = "project_slug",
    project_path   = "project_path",
  }
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
