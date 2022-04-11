
output "gitlab_group_id" {
  description = "The GitLab group id."
  value       = data.gitlab_group.group.id
}

output "registry_deploy_token" {
  description = "The GitLab Deploy Token to access the Docker registry."
  value       = gitlab_deploy_token.regcred.token
  sensitive   = true
}
