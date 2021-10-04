provider "digitalocean" {
  token = var.do_token
}

provider "gitlab" {
  token = var.gitlab_token
}

data "digitalocean_ssh_key" "main" {
  for_each = toset(var.do_20tab_ssh_key_names)
  name = each.value
}
