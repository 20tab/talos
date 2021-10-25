provider "digitalocean" {
  token = var.do_token
}

provider "gitlab" {
  token = var.gitlab_token
}
