terraform {
  required_providers {
    vault = {
      source  = "hashicorp/vault"
      version = "3.6.0"
    }
  }
}

provider "vault" {}

/* Terraform Cloud user */

data "http" "tfc_user_info" {
  count = var.terraform_cloud_token != "" ? 1 : 0

  url = "https://app.terraform.io/api/v2/account/details"

  request_headers = {
    Accept        = "application/json"
    Authorization = "Bearer ${var.terraform_cloud_token}"
  }
}

/* Secrets Engines */

resource "vault_mount" "main" {
  path = var.project_slug

  description = "The ${var.project_name} project secrets."

  type = "kv"
  options = {
    version = "1"
  }
}

resource "vault_terraform_cloud_secret_backend" "main" {
  count = var.terraform_cloud_token != "" ? 1 : 0

  backend = "${var.project_slug}-tfc"

  description = "The ${var.project_name} project Terraform Cloud secrets engine."

  token = var.terraform_cloud_token
}

resource "vault_terraform_cloud_secret_role" "main" {
  count = var.terraform_cloud_token != "" ? 1 : 0

  backend = vault_terraform_cloud_secret_backend.main[0].backend
  name    = var.project_slug
  user_id = jsondecode(data.http.tfc_user_info[0].body).data.id

  max_ttl = var.terraform_cloud_role_max_ttl
  ttl     = var.terraform_cloud_role_ttl
}

/* Secrets */

resource "vault_generic_secret" "common" {
  for_each = var.common_secrets

  path = "${vault_mount.main.path}/common/${each.key}"

  data_json = jsonencode(each.value)
}

resource "vault_generic_secret" "service" {
  for_each = var.service_secrets

  path = "${vault_mount.main.path}/${var.service_slug}/${each.key}"

  data_json = jsonencode(each.value)
}
