package test

import (
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
)

func TestTerraformBootstrap(t *testing.T) {
	// Construct the terraform options with default retryable errors to handle the most common
	// retryable errors in terraform testing.
	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		// Set the path to the Terraform code that will be tested.
		TerraformDir: "../terraform/",
		// VarFiles: []string{"test/bootstrap_test.tfvars_templ"},
	})

	// Clean up resources with "terraform destroy" at the end of the test.
	// defer terraform.Destroy(t, terraformOptions)
	
	// Run "terraform init" and "terraform apply". Fail the test if there are any errors.
	terraform.Init(t, terraformOptions)
	terraform.RunTerraformCommand(t, terraformOptions, "fmt", "-check")
	terraform.Validate(t, terraformOptions)
	// terraform.InitAndPlan(t, terraformOptions)
	// terraform.InitAndApply(t, terraformOptions)
}


func TestTerraformCore(t *testing.T) {
	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../{{cookiecutter.project_dirname}}/terraform/core/digitalocean-k8s/",
	})

	terraform.RunTerraformCommand(t, terraformOptions, "init", "-backend=false")
	terraform.RunTerraformCommand(t, terraformOptions, "fmt", "-check")
	terraform.Validate(t, terraformOptions)
}


func TestTerraformEnvironmentDigitalOcean(t *testing.T) {
	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../{{cookiecutter.project_dirname}}/terraform/environment/digitalocean-k8s/",
	})

	terraform.RunTerraformCommand(t, terraformOptions, "init", "-backend=false")
	terraform.RunTerraformCommand(t, terraformOptions, "fmt", "-check")
	terraform.Validate(t, terraformOptions)
}


func TestTerraformEnvironmentOther(t *testing.T) {
	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../{{cookiecutter.project_dirname}}/terraform/environment/other-k8s/",
	})

	terraform.RunTerraformCommand(t, terraformOptions, "init", "-backend=false")
	terraform.RunTerraformCommand(t, terraformOptions, "fmt", "-check")
	terraform.Validate(t, terraformOptions)
}


func TestTerraformEnvironmentDatabaseDumpCronjobModule(t *testing.T) {
	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../{{cookiecutter.project_dirname}}/terraform/environment/modules/kubernetes/database-dump-cronjob/",
	})

	terraform.RunTerraformCommand(t, terraformOptions, "init", "-backend=false")
	terraform.RunTerraformCommand(t, terraformOptions, "fmt", "-check")
	terraform.Validate(t, terraformOptions)
}


func TestTerraformEnvironmentPostgresModule(t *testing.T) {
	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../{{cookiecutter.project_dirname}}/terraform/environment/modules/kubernetes/postgres/",
	})

	terraform.RunTerraformCommand(t, terraformOptions, "init", "-backend=false")
	terraform.RunTerraformCommand(t, terraformOptions, "fmt", "-check")
	terraform.Validate(t, terraformOptions)
}


func TestTerraformEnvironmentRedisModule(t *testing.T) {
	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../{{cookiecutter.project_dirname}}/terraform/environment/modules/kubernetes/redis/",
	})

	terraform.RunTerraformCommand(t, terraformOptions, "init", "-backend=false")
	terraform.RunTerraformCommand(t, terraformOptions, "fmt", "-check")
	terraform.Validate(t, terraformOptions)
}


func TestTerraformEnvironmentRoutingModule(t *testing.T) {
	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../{{cookiecutter.project_dirname}}/terraform/environment/modules/kubernetes/routing/",
	})

	terraform.RunTerraformCommand(t, terraformOptions, "init", "-backend=false")
	terraform.RunTerraformCommand(t, terraformOptions, "fmt", "-check")
	terraform.Validate(t, terraformOptions)
}


func TestTerraformNetworkingDigitalOcean(t *testing.T) {
	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../{{cookiecutter.project_dirname}}/terraform/networking/digitalocean-k8s/",
	})

	terraform.RunTerraformCommand(t, terraformOptions, "init", "-backend=false")
	terraform.RunTerraformCommand(t, terraformOptions, "fmt", "-check")
	terraform.Validate(t, terraformOptions)
}


func TestTerraformNetworkingOther(t *testing.T) {
	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../{{cookiecutter.project_dirname}}/terraform/networking/other-k8s/",
	})

	terraform.RunTerraformCommand(t, terraformOptions, "init", "-backend=false")
	terraform.RunTerraformCommand(t, terraformOptions, "fmt", "-check")
	terraform.Validate(t, terraformOptions)
}


func TestTerraformNetworkingMonitoringModule(t *testing.T) {
	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../{{cookiecutter.project_dirname}}/terraform/networking/modules/kubernetes/monitoring/",
	})

	terraform.RunTerraformCommand(t, terraformOptions, "init", "-backend=false")
	terraform.RunTerraformCommand(t, terraformOptions, "fmt", "-check")
	terraform.Validate(t, terraformOptions)
}


func TestTerraformNetworkingTraefikModule(t *testing.T) {
	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../{{cookiecutter.project_dirname}}/terraform/networking/modules/kubernetes/traefik/",
	})

	terraform.RunTerraformCommand(t, terraformOptions, "init", "-backend=false")
	terraform.RunTerraformCommand(t, terraformOptions, "fmt", "-check")
	terraform.Validate(t, terraformOptions)
}
