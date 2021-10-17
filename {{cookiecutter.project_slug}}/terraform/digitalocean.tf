resource "digitalocean_kubernetes_cluster" "k8s-cluster" {
  name    = "k8s-${var.project_slug}"
  region  = "fra1"
  version = "1.21.3-do.0"

  node_pool {
    name       = "worker-pool"
    size       = "s-1vcpu-2gb-amd"
    node_count = 2
  }
  provisioner "local-exec" {
    inline = [
      "kubectl --kubeconfig=${self.kube_config[0]} apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v0.44.0/deploy/static/provider/do/deploy.yaml",
      "kubectl --kubeconfig=${self.kube_config[0]} patch svc ingress-nginx-controller -p '{\"spec\":{\"externalTrafficPolicy\": \"Cluster\"}}' -n ingress-nginx"
    ]
  }
}

resource "digitalocean_spaces_bucket" "s3-storage" {
  name   = "${var.project_slug}"
  region = "${digitalocean_kubernetes_cluster.k8s-cluster.region}"
}

resource "digitalocean_database_connection_pool" "db-production-pool" {
  cluster_id = digitalocean_database_cluster.db-postgres.id
  name       = "db-${var.projecT_slug}-production-pool"
  mode       = "transaction"
  size       = 20
  db_name    = "${digitalocean_database_cluster.db-production.name}"
  user       = "db-${var.project_slug}-user"
}

resource "digitalocean_database_db" "db-production" {
  cluster_id = digitalocean_database_cluster.db-postgres.id
  name       = "db-${var.project_slug}-production"
}

resource "digitalocean_database_connection_pool" "db-integration-pool" {
  cluster_id = digitalocean_database_cluster.db-postgres.id
  name       = "db-${var.project_slug}-integration-pool"
  mode       = "transaction"
  size       = 1
  db_name    = "${digitalocean_database_cluster.db-integration.name}"
  user       = "db-${var.project_slug}-user"
}

resource "digitalocean_database_db" "db-integration" {
  cluster_id = digitalocean_database_cluster.db-postgres.id
  name       = "db-${var.project_slug}-integration"
}

resource "digitalocean_database_connection_pool" "db-development-pool" {
  cluster_id = digitalocean_database_cluster.db-postgres.id
  name       = "db-${var.project_slug}-development-pool"
  mode       = "transaction"
  size       = 1
  db_name    = "${digitalocean_database_cluster.db-development.name}"
  user       = "db-${var.project_slug}-user"
}

resource "digitalocean_database_db" "db-development" {
  cluster_id = digitalocean_database_cluster.db-postgres.id
  name       = "db-${var.project_slug}-development"
}

resource "digitalocean_database_user" "db-postgres-user" {
  cluster_id = digitalocean_database_cluster.db-postgres.id
  name       = "db-${var.project_slug}-user"
}

resource "digitalocean_database_cluster" "db-postgres" {
  name       = "db-postgresql-${digitalocean_kubernetes_cluster.k8s-cluster.region}-${var.project_slug}"
  engine     = "pg"
  version    = "13"
  size       = "db-s-1vcpu-1gb"
  region     = "${digitalocean_kubernetes_cluster.k8s-cluster.region}"
  node_count = 1
}

resource "digitalocean_domain" "project-domain" {
  name       = var.project_domain
  ip_address = digitalocean_kubernetes_cluster.k8s-cluster.ipv4_address
}

resource "digitalocean_record" "www" {
  domain = var.project_domain
  type   = "A"
  name   = "www"
  value  = digitalocean_kubernetes_cluster.k8s-cluster.ipv4_address
}

resource "digitalocean_record" "test" {
  domain = var.project_domain
  type   = "A"
  name   = "test"
  value  = digitalocean_kubernetes_cluster.k8s-cluster.ipv4_address
}

resource "digitalocean_record" "dev" {
  domain = var.project_domain
  type   = "A"
  name   = "dev"
  value  = digitalocean_kubernetes_cluster.k8s-cluster.ipv4_address
}

resource "digitalocean_certificate" "ssl-cert" {
  name    = "le-${var.project_slug}"
  type    = "lets_encrypt"
  domains = ["www.${project_domain}", "test.${project_domain}", "dev.${project_domain}"]
}

resource "digitalocean_loadbalancer" "public" {
  name        = "loadbalancer-${var.project_slug}"
  region      = digitalocean_kubernetes_cluster.k8s-cluster.region
  droplet_tag = "backend"

  forwarding_rule {
    entry_port     = 80
    entry_protocol = "http"
    target_port     = 443
    target_protocol = "https"
    certificate_name = digitalocean_certificate.cert.name
  }
}
