resource "gitlab_group" "group" {
  name        = var.project_name
  path        = var.project_slug
  description = "${var.project_name} group"
}

resource "gitlab_project" "orchestrator" {
  name         = "Orchestrator"
  description  = "${var.project_name} orchestrator"
  namespace_id = gitlab_group.group.id
}

resource "gitlab_project" "backend" {
  name         = "Backend"
  description  = "${var.project_name} backend"
  namespace_id = gitlab_group.group.id
}

resource "gitlab_project" "frontend" {
  name         = "Frontend"
  description  = "${var.project_name} frontend"
  namespace_id = gitlab_group.group.id
}

