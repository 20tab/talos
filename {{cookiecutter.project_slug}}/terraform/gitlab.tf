resource "gitlab_group" "group" {
  name        = var.project_name
  path        = var.project_slug
  description = "${var.project_name} group"
}

resource "gitlab_project" "orchestrator" {
  name         = "Orchestrator"
  description  = "${var.project_name} orchestrator"
  namespace_id = gitlab_group.group.id

  provisioner "local-exec" {
    inline = [
      # Update README.md
      "sed -i -e \"s/__GITLAB_GROUP__/${var.project_slug}\" README.md",
      # Initialize orchestrator git repository 
      "./scripts/git_init.sh ${self.ssh_url_to_repo}",
    ]
  }
}

resource "gitlab_project" "backend" {
  name         = "Backend"
  description  = "${var.project_name} backend"
  namespace_id = gitlab_group.group.id

  provisioner "local-exec" {
    inline = [
      # Initialize backend git repository 
      "cd backend && ../scripts/git_init.sh ${self.ssh_url_to_repo}",
    ]
  }
}

resource "gitlab_project_badge" "coverage_backend" {
  project   = gitlab_project.backend.id
  link_url  = "https://${var.project_slug}.gitlab.io/backend/htmlcov/"
  image_url = "https://gitlab.com/\\%\\{project_path}/badges/\\%\\{default_branch}/coverage.svg"
}

resource "gitlab_project_badge" "pipeline_backend" {
  project   = gitlab_project.backend.id
  link_url  = "https://gitlab.com/\\%\\{project_path}/pipelines"
  image_url = "https://gitlab.com/\\%\\{project_path}/badges/\\%\\{default_branch}/pipeline.svg"
}

resource "gitlab_project" "frontend" {
  name         = "Frontend"
  description  = "${var.project_name} frontend"
  namespace_id = gitlab_group.group.id

  provisioner "local-exec" {
    inline = [
      # Initialize frontend git repository 
      "cd frontend && ../scripts/git_init.sh ${self.ssh_url_to_repo}",
    ]
  }
}

resource "gitlab_project_badge" "coverage_frontend" {
  project   = gitlab_project.frontend.id
  link_url  = "https://${var.project_slug}.gitlab.io/frontend/htmlcov/"
  image_url = "https://gitlab.com/\\%\\{project_path}/badges/\\%\\{default_branch}/coverage.svg"
}

resource "gitlab_project_badge" "pipeline_frontend" {
  project   = gitlab_project.frontend.id
  link_url  = "https://gitlab.com/\\%\\{project_path}/pipelines"
  image_url = "https://gitlab.com/\\%\\{project_path}/badges/\\%\\{default_branch}/pipeline.svg"
}

# TODO 
# - setup members
# - setup conditionals resources
# - setup branch protections
