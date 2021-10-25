terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
    gitlab = {
      source = "gitlabhq/gitlab"
      version = "3.3.0"
    }
  }
}
