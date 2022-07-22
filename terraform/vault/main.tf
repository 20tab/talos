terraform {
  backend "local" {
  }

  required_providers {
    vault = {
      source  = "hashicorp/vault"
      version = "3.7.0"
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
  path = var.project_path

  description = "The ${var.project_name} project secrets."

  type = "kv"
  options = {
    version = "1"
  }
}

resource "vault_terraform_cloud_secret_backend" "main" {
  count = var.terraform_cloud_token != "" ? 1 : 0

  backend = "${var.project_path}-tfc"

  description = "The ${var.project_name} project Terraform Cloud secrets engine."

  token = var.terraform_cloud_token
}

resource "vault_terraform_cloud_secret_role" "main" {
  count = var.terraform_cloud_token != "" ? 1 : 0

  backend = vault_terraform_cloud_secret_backend.main[0].backend
  name    = "default"
  user_id = jsondecode(data.http.tfc_user_info[0].body).data.id

  max_ttl = var.terraform_cloud_role_max_ttl
  ttl     = var.terraform_cloud_role_ttl
}

/* Secrets */

resource "vault_generic_secret" "main" {
  for_each = var.secrets

  path = "${vault_mount.main.path}/${each.key}"

  data_json = jsonencode(each.value)
}
