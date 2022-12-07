output "registry_password" {
  description = "The password to access the GitLab images registry."
  sensitive   = true
  value       = gitlab_deploy_token.regcred.token
}

output "registry_username" {
  description = "The username to access the GitLab images registry."
  sensitive   = true
  value       = gitlab_deploy_token.regcred.username
}
