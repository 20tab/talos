terraform {
  required_providers {
    vault = {
      source  = "hashicorp/vault"
      version = "3.6.0"
    }
  }
}

provider "vault" {
}

/* Auth backend */

data "vault_auth_backend" "main" {
  count = var.auth_backend_path != "" ? 1 : 0

  path = var.auth_backend_path
}

/* Policy */

resource "vault_policy" "main" {
  count = var.auth_backend_path != "" ? 1 : 0

  name   = var.project_slug
  policy = <<EOF
# Permissions for the ${var.project_slug} project

path "sys/mounts" {
  capabilities = ["list", "read"]
}

# Manage KV secrets
path "${var.project_slug}/*" {
  capabilities = ["list", "read", "create", "update", "delete"]
}

path "sys/mounts/${var.project_slug}" {
  capabilities = ["create", "update", "delete"]
}

path "${var.project_slug}" {
  capabilities = ["list"]
}

# Manage TFC secrets
path "${var.project_slug}-tfc/*" {
  capabilities = ["list", "read", "create", "update", "delete"]
}

path "sys/mounts/${var.project_slug}-tfc" {
  capabilities = ["create", "update", "delete"]
}

path "${var.project_slug}-tfc" {
  capabilities = ["list"]
}

# Enable ops on children token
path "auth/token/create" {
  capabilities = ["create", "read", "update", "list"]
}
EOF
}

/* Group and Alias */

resource "vault_identity_group" "main" {
  count = var.auth_backend_path != "" ? 1 : 0

  name     = var.project_slug
  type     = "external"
  policies = [vault_policy.main[0].name]
}

resource "vault_identity_group_alias" "main" {
  count = var.auth_backend_path != "" ? 1 : 0

  name           = var.project_slug
  mount_accessor = data.vault_auth_backend.main[0].accessor
  canonical_id   = vault_identity_group.main[0].id
}
