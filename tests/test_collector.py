"""Bootstrap collector tests."""

from contextlib import contextmanager
from io import StringIO
from pathlib import Path
from unittest import TestCase, mock
from bootstrap.collector import Collector
from bootstrap.constants import BASE_DIR


@contextmanager
def input(*cmds):
    """Mock the user input."""
    visible_cmds = "\n".join(c for c in cmds if isinstance(c, str))
    hidden_cmds = [c["hidden"] for c in cmds if isinstance(c, dict) and "hidden" in c]
    with mock.patch("sys.stdin", StringIO(f"{visible_cmds}\n")), mock.patch(
        "getpass.getpass", side_effect=hidden_cmds
    ):
        yield


class TestBootstrapCollector(TestCase):
    """Test the bootstrap collector."""

    maxDiff = None

    def test_project_name_from_input(self):
        """Test collecting the project name from user input."""
        collector = Collector()
        self.assertIsNone(collector.project_name)
        with input("My New Project"):
            collector.set_project_name()
        self.assertEqual(collector.project_name, "My New Project")

    def test_project_name_from_options(self):
        """Test collecting the project name from the collected options."""
        collector = Collector(project_name="My Project")
        self.assertEqual(collector.project_name, "My Project")
        with mock.patch("bootstrap.collector.click.confirm") as mocked_prompt:
            collector.set_project_name()
        self.assertEqual(collector.project_name, "My Project")
        mocked_prompt.assert_not_called()

    def test_project_slug_from_default(self):
        """Test collecting the project slug from its default value."""
        collector = Collector(project_name="My Project")
        self.assertIsNone(collector.project_slug)
        with input(""):
            collector.set_project_slug()
        self.assertEqual(collector.project_slug, "my-project")

    def test_project_slug_from_input(self):
        """Test collecting the project slug from user input."""
        collector = Collector(project_name="Test Project")
        self.assertIsNone(collector.project_slug)
        with input("My New Project Slug"):
            collector.set_project_slug()
        self.assertEqual(collector.project_slug, "my-new-project-slug")

    def test_project_slug_from_options(self):
        """Test collecting the project slug from the collected options."""
        collector = Collector(project_name="My Project", project_slug="my-new-project")
        self.assertEqual(collector.project_slug, "my-new-project")
        with mock.patch("bootstrap.collector.click.prompt") as mocked_prompt:
            collector.set_project_slug()
        self.assertEqual(collector.project_slug, "my-new-project")
        mocked_prompt.assert_not_called()

    def test_project_dirname(self):
        """Test collecting the project dirname."""
        collector = Collector(project_slug="test-project")
        self.assertIsNone(collector.project_dirname)
        collector.set_project_dirname()
        self.assertEqual(collector.project_dirname, "testproject")

    def test_service_dir_new(self):
        """Test collecting the service directory, and the dir does not exist yet."""
        MockedPath = mock.MagicMock(spec=Path)
        output_dir = MockedPath("mocked-output-dir")
        output_dir.is_absolute.return_value = True
        service_dir = MockedPath("mocked-output-dir/my-project")
        service_dir.is_dir.return_value = False
        output_dir.__truediv__.return_value = service_dir
        collector = Collector(project_slug="my-project")
        self.assertIsNone(collector._service_dir)
        collector.output_dir = output_dir
        collector.set_project_dirname()
        collector.set_service_dir()
        output_dir.__truediv__.assert_called_once_with("myproject")
        self.assertEqual(collector._service_dir, service_dir)

    def test_service_dir_existing(self):
        """Test collecting the service directory, and the dir already exists."""
        MockedPath = mock.MagicMock(spec=Path)
        output_dir = MockedPath("mocked-output-dir")
        output_dir.is_absolute.return_value = True
        service_dir = MockedPath("mocked-output-dir/my-project")
        service_dir.is_dir.return_value = True
        output_dir.__truediv__.return_value = service_dir
        collector = Collector(project_slug="my-project")
        self.assertIsNone(collector._service_dir)
        collector.output_dir = output_dir
        collector.set_project_dirname()
        with mock.patch("bootstrap.collector.rmtree") as mocked_rmtree, input("y"):
            collector.set_service_dir()
        output_dir.__truediv__.assert_called_once_with("myproject")
        mocked_rmtree.assert_called_once_with(service_dir)
        self.assertEqual(collector._service_dir, service_dir)

    def test_backend_service_none(self):
        """Test setting up the 'none' backend service."""
        collector = Collector(backend_type="none")
        self.assertEqual(collector.backend_type, "none")
        self.assertIsNone(collector.backend_service_slug)
        with mock.patch("bootstrap.collector.click.prompt") as mocked_prompt:
            collector.set_backend_service()
        self.assertEqual(collector.backend_type, "none")
        self.assertIsNone(collector.backend_service_slug)
        mocked_prompt.assert_not_called()

    def test_backend_service_django_and_slug_from_default(self):
        """Test setting up the 'django' backend service with default slug."""
        collector = Collector(backend_type="django")
        self.assertEqual(collector.backend_type, "django")
        self.assertIsNone(collector.backend_service_slug)
        with input(""):
            collector.set_backend_service()
        self.assertEqual(collector.backend_type, "django")
        self.assertEqual(collector.backend_service_slug, "backend")

    def test_backend_service_django_and_slug_from_input(self):
        """Test setting up the 'django' backend service taking slug from user input."""
        collector = Collector(backend_type="django")
        self.assertEqual(collector.backend_type, "django")
        self.assertIsNone(collector.backend_service_slug)
        with input("my-django-service"):
            collector.set_backend_service()
        self.assertEqual(collector.backend_type, "django")
        self.assertEqual(collector.backend_service_slug, "mydjangoservice")

    def test_backend_service_invalid(self):
        """Test trying to set up an invalid backend service type."""
        collector = Collector(backend_type="bad-type")
        self.assertEqual(collector.backend_type, "bad-type")
        self.assertIsNone(collector.backend_service_slug)
        with input("another-bad-type", "yet-another-bad-type", "django", ""):
            collector.set_backend_service()
        self.assertEqual(collector.backend_type, "django")
        self.assertEqual(collector.backend_service_slug, "backend")

    def test_frontend_service_none(self):
        """Test setting up the 'none' frontend service."""
        collector = Collector(frontend_type="none")
        self.assertEqual(collector.frontend_type, "none")
        self.assertIsNone(collector.frontend_service_slug)
        with mock.patch("bootstrap.collector.click.prompt") as mocked_prompt:
            collector.set_frontend_service()
        self.assertEqual(collector.frontend_type, "none")
        self.assertIsNone(collector.frontend_service_slug)
        mocked_prompt.assert_not_called()

    def test_frontend_service_nextjs_and_slug_from_default(self):
        """Test setting up the 'nextjs' frontend service with default slug."""
        collector = Collector(frontend_type="nextjs")
        self.assertEqual(collector.frontend_type, "nextjs")
        self.assertIsNone(collector.frontend_service_slug)
        with input(""):
            collector.set_frontend_service()
        self.assertEqual(collector.frontend_type, "nextjs")
        self.assertEqual(collector.frontend_service_slug, "frontend")

    def test_frontend_service_nextjs_and_slug_from_input(self):
        """Test setting up the 'nextjs' frontend service taking slug from user input."""
        collector = Collector(frontend_type="nextjs")
        self.assertEqual(collector.frontend_type, "nextjs")
        self.assertIsNone(collector.frontend_service_slug)
        with input("my-nextjs-service"):
            collector.set_frontend_service()
        self.assertEqual(collector.frontend_type, "nextjs")
        self.assertEqual(collector.frontend_service_slug, "mynextjsservice")

    def test_frontend_service_invalid(self):
        """Test trying to set up an invalid frontend service type."""
        collector = Collector(frontend_type="bad-type")
        self.assertEqual(collector.frontend_type, "bad-type")
        self.assertIsNone(collector.frontend_service_slug)
        with input("another-bad-type", "yet-another-bad-type", "nextjs", ""):
            collector.set_frontend_service()
        self.assertEqual(collector.frontend_type, "nextjs")
        self.assertEqual(collector.frontend_service_slug, "frontend")

    def test_use_redis_from_input(self):
        """Test setting the `use_redis` flag from user input."""
        collector = Collector()
        self.assertIsNone(collector.use_redis)
        with input("y"):
            collector.set_use_redis()
        self.assertTrue(collector.use_redis)

    def test_use_redis_from_options(self):
        """Test setting the `use_redis` flag from user input."""
        collector = Collector(use_redis=False)
        self.assertFalse(collector.use_redis)
        with mock.patch("bootstrap.collector.click.confirm") as mocked_confirm:
            collector.set_use_redis()
        self.assertFalse(collector.use_redis)
        mocked_confirm.assert_not_called()

    def test_terraform_backend_from_default(self):
        """Test setting the Terraform backend from its default value."""
        collector = Collector()
        self.assertIsNone(collector.terraform_backend)
        collector.set_terraform_cloud = mock.MagicMock()
        with input(""):
            collector.set_terraform()
        self.assertEqual(collector.terraform_backend, "terraform-cloud")
        collector.set_terraform_cloud.assert_called_once()

    def test_terraform_backend_from_input(self):
        """Test setting the Terraform backend from user input."""
        collector = Collector()
        self.assertIsNone(collector.terraform_backend)
        collector.set_terraform_cloud = mock.MagicMock()
        with input("bad-tf-backend", "another-bad-tf-backend", "gitlab"):
            collector.set_terraform()
        self.assertEqual(collector.terraform_backend, "gitlab")
        collector.set_terraform_cloud.assert_not_called()

    def test_terraform_backend_from_options(self):
        """Test setting the Terraform backend from the collected options."""
        collector = Collector(terraform_backend="terraform-cloud")
        self.assertEqual(collector.terraform_backend, "terraform-cloud")
        collector.set_terraform_cloud = mock.MagicMock()
        with mock.patch("bootstrap.collector.click") as mocked_click:
            collector.set_terraform()
        self.assertEqual(collector.terraform_backend, "terraform-cloud")
        mocked_click.prompt.assert_not_called()
        collector.set_terraform_cloud.assert_called_once()

    def test_terraform_cloud_from_input(self):
        """Test setting up Terraform Cloud from user input."""
        collector = Collector(terraform_backend="terraform-cloud")
        self.assertIsNone(collector.terraform_cloud_hostname)
        self.assertIsNone(collector.terraform_cloud_token)
        self.assertIsNone(collector.terraform_cloud_organization)
        self.assertIsNone(collector.terraform_cloud_organization_create)
        self.assertIsNone(collector.terraform_cloud_admin_email)
        with input(
            "",
            {"hidden": "mytfcT0k3N"},
            "myTFCOrg",
            "y",
            "bad-email",
            "admin@test.com",
        ):
            collector.set_terraform_cloud()
        self.assertEqual(collector.terraform_cloud_hostname, "app.terraform.io")
        self.assertEqual(collector.terraform_cloud_token, "mytfcT0k3N")
        self.assertEqual(collector.terraform_cloud_organization, "myTFCOrg")
        self.assertTrue(collector.terraform_cloud_organization_create)
        self.assertEqual(collector.terraform_cloud_admin_email, "admin@test.com")

    def test_terraform_cloud_from_options(self):
        """Test setting up Terraform Cloud from the collected options."""
        collector = Collector(
            terraform_backend="terraform-cloud",
            terraform_cloud_hostname="app.terraform.io",
            terraform_cloud_token="mytfcT0k3N",
            terraform_cloud_organization="myTFCOrg",
            terraform_cloud_organization_create=True,
            terraform_cloud_admin_email="admin@test.com",
        )
        self.assertEqual(collector.terraform_cloud_hostname, "app.terraform.io")
        self.assertEqual(collector.terraform_cloud_token, "mytfcT0k3N")
        self.assertEqual(collector.terraform_cloud_organization, "myTFCOrg")
        self.assertTrue(collector.terraform_cloud_organization_create)
        self.assertEqual(collector.terraform_cloud_admin_email, "admin@test.com")
        with mock.patch("bootstrap.collector.click") as mocked_click:
            collector.set_terraform_cloud()
        self.assertEqual(collector.terraform_cloud_hostname, "app.terraform.io")
        self.assertEqual(collector.terraform_cloud_token, "mytfcT0k3N")
        self.assertEqual(collector.terraform_cloud_organization, "myTFCOrg")
        self.assertTrue(collector.terraform_cloud_organization_create)
        self.assertEqual(collector.terraform_cloud_admin_email, "admin@test.com")
        mocked_click.prompt.assert_not_called()

    def test_terraform_cloud_from_input_and_options(self):
        """Test setting up Terraform Cloud from options and user input."""
        collector = Collector(
            terraform_backend="terraform-cloud",
            terraform_cloud_token="mytfcT0k3N",
        )
        self.assertIsNone(collector.terraform_cloud_hostname)
        self.assertEqual(collector.terraform_cloud_token, "mytfcT0k3N")
        self.assertIsNone(collector.terraform_cloud_organization)
        self.assertIsNone(collector.terraform_cloud_organization_create)
        self.assertIsNone(collector.terraform_cloud_admin_email)
        with input("tfc.my-company.com", "myTFCOrg", "n"):
            collector.set_terraform_cloud()
        self.assertEqual(collector.terraform_cloud_hostname, "tfc.my-company.com")
        self.assertEqual(collector.terraform_cloud_token, "mytfcT0k3N")
        self.assertEqual(collector.terraform_cloud_organization, "myTFCOrg")
        self.assertFalse(collector.terraform_cloud_organization_create)
        self.assertEqual(collector.terraform_cloud_admin_email, "")

    def test_vault_no(self):
        """Test not setting vault."""
        collector = Collector()
        self.assertIsNone(collector.vault_token)
        self.assertIsNone(collector.vault_url)
        with input("n"):
            collector.set_vault()
        self.assertIsNone(collector.vault_token)

    def test_vault_from_input(self):
        """Test setting up Vault from user input."""
        collector = Collector()
        self.assertIsNone(collector.vault_token)
        self.assertIsNone(collector.vault_url)
        with input({"hidden": "v4UlTtok3N"}, "https://vault.test.com",), mock.patch(
            "bootstrap.collector.click.confirm", return_value=True
        ) as mocked_confirm:
            collector.set_vault()
        self.assertEqual(collector.vault_token, "v4UlTtok3N")
        self.assertEqual(collector.vault_url, "https://vault.test.com")
        self.assertEqual(len(mocked_confirm.mock_calls), 2)

    def test_vault_from_options(self):
        """Test setting up Vault from the collected options."""
        collector = Collector(
            vault_token="v4UlTtok3N", vault_url="https://vault.test.com"
        )
        self.assertEqual(collector.vault_token, "v4UlTtok3N")
        self.assertEqual(collector.vault_url, "https://vault.test.com")
        with mock.patch(
            "bootstrap.collector.click.confirm", return_value=True
        ) as mocked_confirm:
            collector.set_vault()
        self.assertEqual(collector.vault_token, "v4UlTtok3N")
        self.assertEqual(collector.vault_url, "https://vault.test.com")
        self.assertEqual(len(mocked_confirm.mock_calls), 1)

    def test_vault_from_input_and_options(self):
        """Test setting up Vault from options and user input."""
        collector = Collector(vault_url="https://vault.test.com")
        self.assertIsNone(collector.vault_token)
        self.assertEqual(collector.vault_url, "https://vault.test.com")
        with input({"hidden": "v4UlTtok3N"}), mock.patch(
            "bootstrap.collector.click.confirm", return_value=True
        ) as mocked_confirm:
            collector.set_vault()
        self.assertEqual(collector.vault_token, "v4UlTtok3N")
        self.assertEqual(collector.vault_url, "https://vault.test.com")
        self.assertEqual(len(mocked_confirm.mock_calls), 1)

    def test_deployment_type_from_default(self):
        """Test collecting the deployment type from its default value."""
        collector = Collector()
        self.assertIsNone(collector.deployment_type)
        with input(""):
            collector.set_deployment_type()
        self.assertEqual(collector.deployment_type, "digitalocean-k8s")

    def test_deployment_type_from_input(self):
        """Test collecting the deployment type from user input."""
        collector = Collector()
        self.assertIsNone(collector.deployment_type)
        with input("bad-deployment-type", "yet-another-bad-value", "other-k8s"):
            collector.set_deployment_type()
        self.assertEqual(collector.deployment_type, "other-k8s")

    def test_deployment_type_from_options(self):
        """Test collecting the deployment type from the collected options."""
        collector = Collector(deployment_type="other-k8s")
        self.assertEqual(collector.deployment_type, "other-k8s")
        with mock.patch("bootstrap.collector.click.prompt") as mocked_prompt:
            collector.set_deployment_type()
        self.assertEqual(collector.deployment_type, "other-k8s")
        mocked_prompt.assert_not_called()

    def test_environments_distribution_for_other_k8s_deployment(self):
        """Test collecting the environments distribution for other-k8s deployment."""
        collector = Collector(deployment_type="other-k8s")
        self.assertIsNone(collector.environments_distribution)
        with mock.patch("bootstrap.collector.click.prompt") as mocked_prompt:
            collector.set_environments_distribution()
        self.assertEqual(collector.environments_distribution, "1")
        mocked_prompt.assert_not_called()

    def test_environments_distribution_from_default(self):
        """Test collecting the environments distribution from its default value."""
        collector = Collector()
        self.assertIsNone(collector.environments_distribution)
        with input(""):
            collector.set_environments_distribution()
        self.assertEqual(collector.environments_distribution, "1")

    def test_environments_distribution_from_input(self):
        """Test collecting the environments distribution from user input."""
        collector = Collector()
        self.assertIsNone(collector.environments_distribution)
        with input("one", "yet-another-bad-value", "3"):
            collector.set_environments_distribution()
        self.assertEqual(collector.environments_distribution, "3")

    def test_environments_distribution_from_options(self):
        """Test collecting the environments distribution from the collected options."""
        collector = Collector(environments_distribution="2")
        self.assertEqual(collector.environments_distribution, "2")
        with mock.patch("bootstrap.collector.click.prompt") as mocked_prompt:
            collector.set_environments_distribution()
        self.assertEqual(collector.environments_distribution, "2")
        mocked_prompt.assert_not_called()

    def test_set_domain_and_urls_from_default(self):
        """Test collecting the domain and urls options from default."""
        collector = Collector(project_slug="test-project")
        self.assertIsNone(collector.project_domain)
        self.assertIsNone(collector.subdomain_dev)
        self.assertIsNone(collector.subdomain_stage)
        self.assertIsNone(collector.subdomain_prod)
        self.assertIsNone(collector.project_url_dev)
        self.assertIsNone(collector.project_url_stage)
        self.assertIsNone(collector.project_url_prod)
        self.assertIsNone(collector.subdomain_monitoring)
        with input("", "", "", "", "y", ""):
            collector.set_domain_and_urls()
        self.assertEqual(collector.project_domain, "test-project.com")
        self.assertEqual(collector.project_url_dev, "https://dev.test-project.com")
        self.assertEqual(collector.project_url_stage, "https://stage.test-project.com")
        self.assertEqual(collector.project_url_prod, "https://www.test-project.com")
        self.assertEqual(collector.subdomain_dev, "dev")
        self.assertEqual(collector.subdomain_stage, "stage")
        self.assertEqual(collector.subdomain_prod, "www")
        self.assertEqual(collector.subdomain_monitoring, "logs")

    def test_set_domain_and_urls_from_input(self):
        """Test collecting the domain and urls options from input."""
        collector = Collector(project_slug="test-project")
        self.assertIsNone(collector.project_domain)
        self.assertIsNone(collector.subdomain_dev)
        self.assertIsNone(collector.subdomain_stage)
        self.assertIsNone(collector.subdomain_prod)
        self.assertIsNone(collector.project_url_dev)
        self.assertIsNone(collector.project_url_stage)
        self.assertIsNone(collector.project_url_prod)
        with input(
            "bad domain.com",
            "domain.com",
            "dev from input",
            "   stage-from-Input",
            "prod-from-input             ",
            "n",
        ):
            collector.set_domain_and_urls()
        self.assertEqual(collector.project_domain, "domain.com")
        self.assertEqual(collector.project_url_dev, "https://dev-from-input.domain.com")
        self.assertEqual(
            collector.project_url_stage, "https://stage-from-input.domain.com"
        )
        self.assertEqual(
            collector.project_url_prod, "https://prod-from-input.domain.com"
        )
        self.assertEqual(collector.subdomain_dev, "dev-from-input")
        self.assertEqual(collector.subdomain_stage, "stage-from-input")
        self.assertEqual(collector.subdomain_prod, "prod-from-input")

    def test_set_domain_and_urls_from_options(self):
        """Test collecting the domain and urls options from input."""
        collector = Collector(
            project_slug="test-project",
            project_domain="domain.com",
            subdomain_dev="custom-dev",
            subdomain_stage="custom-stage",
            subdomain_prod="custom-www",
            subdomain_monitoring="custom-log",
        )
        self.assertEqual(collector.project_domain, "domain.com")
        self.assertIsNone(collector.project_url_dev)
        self.assertIsNone(collector.project_url_stage)
        self.assertIsNone(collector.project_url_prod)
        self.assertEqual(collector.subdomain_dev, "custom-dev")
        self.assertEqual(collector.subdomain_stage, "custom-stage")
        self.assertEqual(collector.subdomain_prod, "custom-www")
        with mock.patch("bootstrap.collector.click.prompt") as mocked_prompt:
            collector.set_domain_and_urls()
        self.assertEqual(collector.project_domain, "domain.com")
        self.assertEqual(collector.project_url_dev, "https://custom-dev.domain.com")
        self.assertEqual(collector.project_url_stage, "https://custom-stage.domain.com")
        self.assertEqual(collector.project_url_prod, "https://custom-www.domain.com")
        self.assertEqual(collector.subdomain_dev, "custom-dev")
        self.assertEqual(collector.subdomain_stage, "custom-stage")
        self.assertEqual(collector.subdomain_prod, "custom-www")
        self.assertEqual(collector.subdomain_monitoring, "custom-log")
        mocked_prompt.assert_not_called()

    def test_letsencrypt_from_input_true(self):
        """Test collecting the certificate email from user input."""
        collector = Collector()
        self.assertIsNone(collector.letsencrypt_certificate_email)
        with input(
            "y",
            "not an email",
            "bad email @ really -bad . com      ",
            "admin@admin.com",
        ):
            collector.set_letsencrypt()
        self.assertEqual(collector.letsencrypt_certificate_email, "admin@admin.com")

    def test_letsencrypt_from_input_false(self):
        """Test collecting the certificate email from user input."""
        collector = Collector()
        self.assertIsNone(collector.letsencrypt_certificate_email)
        with input("n"):
            collector.set_letsencrypt()
        self.assertIsNone(collector.letsencrypt_certificate_email)

    def test_letsencrypt_from_options(self):
        """Test collecting the certificate email from the collected options."""
        collector = Collector(letsencrypt_certificate_email="admin@admin.com")
        self.assertEqual(collector.letsencrypt_certificate_email, "admin@admin.com")
        with mock.patch("bootstrap.collector.click.prompt") as mocked_prompt:
            collector.set_letsencrypt()
        self.assertEqual(collector.letsencrypt_certificate_email, "admin@admin.com")
        mocked_prompt.assert_not_called()

    def test_deployment_digitalocean(self):
        """Test setting a DigitalOcean deployment."""
        collector = Collector(deployment_type="digitalocean-k8s")
        collector.set_digitalocean = mock.MagicMock()
        collector.set_deployment()
        collector.set_digitalocean.assert_called_once()

    def test_deployment_other_k8s(self):
        """Test setting a generic Kubernetes deployment."""
        collector = Collector(deployment_type="other-k8s")
        collector.set_kubernetes = mock.MagicMock()
        collector.set_deployment()
        collector.set_kubernetes.assert_called_once()

    def test_deployment_invalid(self):
        """Test setting an invalid deployment."""
        collector = Collector(deployment_type="invalid-deployment")
        self.assertRaises(ValueError, collector.set_deployment)

    def test_digitalocean_default(self):
        """Test setting the Digitalocean options from default."""
        collector = Collector(use_redis=False)
        collector.set_digitalocean_token = mock.MagicMock()
        self.assertFalse(collector._digitalocean_enabled)
        self.assertIsNone(collector.digitalocean_domain_create)
        self.assertIsNone(collector.digitalocean_dns_records_create)
        self.assertIsNone(collector.digitalocean_k8s_cluster_region)
        self.assertIsNone(collector.digitalocean_database_cluster_region)
        self.assertIsNone(collector.digitalocean_database_cluster_node_size)
        with input("", "", "", "", ""):
            collector.set_digitalocean()
        self.assertEqual(collector._digitalocean_enabled, True)
        self.assertEqual(collector.digitalocean_domain_create, True)
        self.assertEqual(collector.digitalocean_dns_records_create, True)
        self.assertEqual(collector.digitalocean_k8s_cluster_region, "fra1")
        self.assertEqual(collector.digitalocean_database_cluster_region, "fra1")
        self.assertEqual(
            collector.digitalocean_database_cluster_node_size, "db-s-1vcpu-2gb"
        )

    def test_digitalocean_input(self):
        """Test setting the Digitalocean options from input."""
        collector = Collector(use_redis=True)
        collector.set_digitalocean_token = mock.MagicMock()
        self.assertFalse(collector._digitalocean_enabled)
        self.assertIsNone(collector.digitalocean_domain_create)
        self.assertIsNone(collector.digitalocean_dns_records_create)
        self.assertIsNone(collector.digitalocean_k8s_cluster_region)
        self.assertIsNone(collector.digitalocean_database_cluster_region)
        self.assertIsNone(collector.digitalocean_database_cluster_node_size)
        with input(
            "n",
            "y",
            "k8s-cluster-region",
            "database-cluster-region",
            "db-size",
            "",
            "redis-cluster-size",
        ):
            collector.set_digitalocean()
        self.assertEqual(collector._digitalocean_enabled, True)
        self.assertEqual(collector.digitalocean_domain_create, False)
        self.assertEqual(collector.digitalocean_dns_records_create, True)
        self.assertEqual(
            collector.digitalocean_k8s_cluster_region, "k8s-cluster-region"
        )
        self.assertEqual(
            collector.digitalocean_database_cluster_region, "database-cluster-region"
        )
        self.assertEqual(collector.digitalocean_database_cluster_node_size, "db-size")
        self.assertEqual(collector.digitalocean_redis_cluster_region, "fra1")
        self.assertEqual(
            collector.digitalocean_redis_cluster_node_size, "redis-cluster-size"
        )

    def test_digitalocean_options(self):
        """Test setting the Digitalocean options from options."""
        collector = Collector(
            use_redis=True,
            digitalocean_redis_cluster_region="fra2",
            digitalocean_redis_cluster_node_size="size",
            digitalocean_domain_create=False,
            digitalocean_dns_records_create=True,
            digitalocean_k8s_cluster_region="k8s-cluster-region-from-options",
            digitalocean_database_cluster_region="database-cluster-region-from-options",
            digitalocean_database_cluster_node_size="db-size-from-options",
        )
        collector.set_digitalocean_token = mock.MagicMock()
        self.assertEquals(collector._digitalocean_enabled, False)
        self.assertEquals(collector.digitalocean_domain_create, False)
        self.assertEquals(collector.digitalocean_dns_records_create, True)
        self.assertEquals(
            collector.digitalocean_k8s_cluster_region, "k8s-cluster-region-from-options"
        )
        self.assertEquals(
            collector.digitalocean_database_cluster_region,
            "database-cluster-region-from-options",
        )
        self.assertEquals(
            collector.digitalocean_database_cluster_node_size, "db-size-from-options"
        )
        with input(
            "n", "y", "k8s-cluster-region", "database-cluster-region", "db-size"
        ):
            collector.set_digitalocean()
        self.assertEquals(collector._digitalocean_enabled, True)
        self.assertEquals(collector.digitalocean_domain_create, False)
        self.assertEquals(collector.digitalocean_dns_records_create, True)
        self.assertEquals(
            collector.digitalocean_k8s_cluster_region, "k8s-cluster-region-from-options"
        )
        self.assertEquals(
            collector.digitalocean_database_cluster_region,
            "database-cluster-region-from-options",
        )
        self.assertEquals(
            collector.digitalocean_database_cluster_node_size, "db-size-from-options"
        )

    def test_digitalocean_token_input(self):
        """Test setting the DigitalOcean token from input."""
        collector = Collector()
        self.assertIsNone(collector.digitalocean_token)
        with input(
            {"hidden": "bad"}, {"hidden": "bad2"}, {"hidden": "more-than-8-chars"}
        ):
            collector.set_digitalocean_token()
        self.assertEquals(collector.digitalocean_token, "more-than-8-chars")

    def test_digitalocean_token_options(self):
        """Test setting the DigitalOcean token from options."""
        collector = Collector(digitalocean_token="options-token")
        collector.set_digitalocean_token()
        self.assertEquals(collector.digitalocean_token, "options-token")

    def test_kubernetes_input_redis(self):
        """Test setting Kubernets options from input with redis."""
        collector = Collector(use_redis=True)
        collector.set_digitalocean_token = mock.MagicMock()
        self.assertFalse(collector._other_kubernetes_enabled)
        self.assertIsNone(collector.kubernetes_cluster_ca_certificate)
        self.assertIsNone(collector.kubernetes_host)
        self.assertIsNone(collector.kubernetes_token)
        self.assertIsNone(collector.postgres_image)
        self.assertIsNone(collector.postgres_persistent_volume_capacity)
        self.assertIsNone(collector.postgres_persistent_volume_claim_capacity)
        self.assertIsNone(collector.postgres_persistent_volume_host_path)
        certificate_path = str(BASE_DIR / "tests/fake_certificate")
        with input(
            certificate_path,
            "https://www.google.com",
            {"hidden": "toKenl0ngeR!"},
            "",
            "",
            "persistent/host/path",
            "",
        ):
            collector.set_kubernetes()
        self.assertTrue(collector._other_kubernetes_enabled)
        self.assertEqual(collector.kubernetes_cluster_ca_certificate, certificate_path)
        self.assertEqual(collector.kubernetes_host, "https://www.google.com")
        self.assertEqual(collector.kubernetes_token, "toKenl0ngeR!")
        self.assertEqual(collector.postgres_image, "postgres:14")
        self.assertEqual(collector.postgres_persistent_volume_capacity, "10Gi")
        self.assertEqual(collector.postgres_persistent_volume_claim_capacity, "")
        self.assertEqual(
            collector.postgres_persistent_volume_host_path, "persistent/host/path"
        )
        self.assertEqual(collector.redis_image, "redis:6.2")

    def test_kubernetes_input_no_redis(self):
        """Test setting Kubernets options from input without redis."""
        collector = Collector(use_redis=False)
        collector.set_digitalocean_token = mock.MagicMock()
        self.assertFalse(collector._other_kubernetes_enabled)
        self.assertIsNone(collector.kubernetes_cluster_ca_certificate)
        self.assertIsNone(collector.kubernetes_host)
        self.assertIsNone(collector.kubernetes_token)
        self.assertIsNone(collector.postgres_image)
        self.assertIsNone(collector.postgres_persistent_volume_capacity)
        self.assertIsNone(collector.postgres_persistent_volume_claim_capacity)
        self.assertIsNone(collector.postgres_persistent_volume_host_path)
        certificate_path = str(BASE_DIR / "tests/fake_certificate")
        with input(
            certificate_path,
            "https://www.google.com",
            {"hidden": "toKenl0ngeR!"},
            "",
            "",
            "persistent/host/path",
        ):
            collector.set_kubernetes()
        self.assertTrue(collector._other_kubernetes_enabled)
        self.assertEqual(collector.kubernetes_cluster_ca_certificate, certificate_path)
        self.assertEqual(collector.kubernetes_host, "https://www.google.com")
        self.assertEqual(collector.kubernetes_token, "toKenl0ngeR!")
        self.assertEqual(collector.postgres_image, "postgres:14")
        self.assertEqual(collector.postgres_persistent_volume_capacity, "10Gi")
        self.assertEqual(collector.postgres_persistent_volume_claim_capacity, "")
        self.assertEqual(
            collector.postgres_persistent_volume_host_path, "persistent/host/path"
        )
        self.assertEqual(collector.redis_image, "")

    def test_sentry_no(self):
        """Test not setting Sentry."""
        collector = Collector(
            backend_service_slug="backend-slug", frontend_service_slug="frontend-slug"
        )
        self.assertIsNone(collector.sentry_org)
        with input("n"):
            collector.set_sentry()
        self.assertIsNone(collector.sentry_org)

    def test_sentry_default(self):
        """Test setting Sentry options from default."""
        collector = Collector(
            backend_service_slug="backend-slug", frontend_service_slug="frontend-slug"
        )
        self.assertIsNone(collector.sentry_org)
        self.assertIsNone(collector.sentry_url)
        self.assertIsNone(collector.sentry_auth_token)
        with input(
            "y",
            "sentry-input-organization",
            "",
            {"hidden": "s3ntrY-4uth-t0kEn!"},
            "",
            "https://backend.sentry.dsn",
            "https://frontend.sentry.dsn",
        ):
            collector.set_sentry()
        self.assertEqual(collector.sentry_org, "sentry-input-organization")
        self.assertEqual(collector.sentry_url, "https://sentry.io")
        self.assertEqual(collector.sentry_auth_token, "s3ntrY-4uth-t0kEn!")

    def test_sentry_options(self):
        """Test setting Sentry options from options."""
        collector = Collector(
            backend_service_slug="backend-slug",
            frontend_service_slug="frontend-slug",
            sentry_org="sentry-options-organization",
            sentry_url="https://other-sentry-url.com",
            sentry_auth_token="S0me!tok3n",
            backend_sentry_dsn="https://backend.sentry.dsn",
            frontend_sentry_dsn="https://frontend.sentry.dsn",
        )
        self.assertEqual(collector.sentry_org, "sentry-options-organization")
        self.assertEqual(collector.sentry_url, "https://other-sentry-url.com")
        self.assertEqual(collector.sentry_auth_token, "S0me!tok3n")
        collector.set_sentry()
        self.assertEqual(collector.sentry_org, "sentry-options-organization")
        self.assertEqual(collector.sentry_url, "https://other-sentry-url.com")
        self.assertEqual(collector.sentry_auth_token, "S0me!tok3n")

    def test_pact_default(self):
        """Test setting Pact options from default."""
        collector = Collector()
        self.assertIsNone(collector.pact_broker_url)
        self.assertIsNone(collector.pact_broker_username)
        self.assertIsNone(collector.pact_broker_password)
        with input(""):
            collector.set_pact()
        self.assertIsNone(collector.pact_broker_url)
        self.assertIsNone(collector.pact_broker_username)
        self.assertIsNone(collector.pact_broker_password)

    def test_pact_input(self):
        """Test setting Pact options from input."""
        collector = Collector()
        self.assertIsNone(collector.pact_broker_url)
        self.assertIsNone(collector.pact_broker_username)
        self.assertIsNone(collector.pact_broker_password)
        with input(
            "y", "https://broker.url", "broker-username", {"hidden": "P4sSw0rd!"}
        ):
            collector.set_pact()
        self.assertEqual(collector.pact_broker_url, "https://broker.url")
        self.assertEqual(collector.pact_broker_username, "broker-username")
        self.assertEqual(collector.pact_broker_password, "P4sSw0rd!")

    def test_pact_options(self):
        """Test setting Pact options from options."""
        collector = Collector(
            pact_broker_url="https://options.broker.url",
            pact_broker_username="options-username",
            pact_broker_password="PassW0rd FroM opt1ons!",
        )
        self.assertEqual(collector.pact_broker_url, "https://options.broker.url")
        self.assertEqual(collector.pact_broker_username, "options-username")
        self.assertEqual(collector.pact_broker_password, "PassW0rd FroM opt1ons!")
        collector.set_pact()
        self.assertEqual(collector.pact_broker_url, "https://options.broker.url")
        self.assertEqual(collector.pact_broker_username, "options-username")
        self.assertEqual(collector.pact_broker_password, "PassW0rd FroM opt1ons!")

    def test_gitlab_no(self):
        """Test not setting Gitlab."""
        collector = Collector(gitlab_url="")
        with input("n"):
            collector.set_gitlab()
        self.assertEqual(collector.gitlab_url, "")

    def test_gitlab_default(self):
        """Test setting Gitlab options from default."""
        collector = Collector(project_slug="gitlab-project")
        self.assertIsNone(collector.gitlab_url)
        self.assertIsNone(collector.gitlab_token)
        self.assertIsNone(collector.gitlab_namespace_path)
        self.assertIsNone(collector.gitlab_group_slug)
        self.assertIsNone(collector.gitlab_group_owners)
        self.assertIsNone(collector.gitlab_group_maintainers)
        self.assertIsNone(collector.gitlab_group_developers)
        with input("", "", {"hidden": "G1tl4b_Tok3n!"}, "", "", "y", "", "", ""):
            collector.set_gitlab()
        self.assertEqual(collector.gitlab_url, "https://gitlab.com")
        self.assertEqual(collector.gitlab_token, "G1tl4b_Tok3n!")
        self.assertEqual(collector.gitlab_namespace_path, "")
        self.assertEqual(collector.gitlab_group_slug, "gitlab-project")
        self.assertEqual(collector.gitlab_group_owners, "")
        self.assertEqual(collector.gitlab_group_maintainers, "")
        self.assertEqual(collector.gitlab_group_developers, "")

    def test_gitlab_input(self):
        """Test setting Gitlab options from input."""
        collector = Collector()
        self.assertIsNone(collector.gitlab_url)
        self.assertIsNone(collector.gitlab_token)
        self.assertIsNone(collector.gitlab_namespace_path)
        self.assertIsNone(collector.gitlab_group_slug)
        self.assertIsNone(collector.gitlab_group_owners)
        self.assertIsNone(collector.gitlab_group_maintainers)
        self.assertIsNone(collector.gitlab_group_developers)
        with input(
            "y",
            "https://gitlab.custom-domain.com",
            {"hidden": "input-G1tl4b_Tok3n!"},
            "inputnamespacepath",
            "input-gitlab-project",
            "owner1,owner2",
            "maintainer1,maintainer2",
            "developer1,developer2",
        ):
            collector.set_gitlab()
        self.assertEqual(collector.gitlab_url, "https://gitlab.custom-domain.com")
        self.assertEqual(collector.gitlab_token, "input-G1tl4b_Tok3n!")
        self.assertEqual(collector.gitlab_namespace_path, "inputnamespacepath")
        self.assertEqual(collector.gitlab_group_slug, "input-gitlab-project")
        self.assertEqual(collector.gitlab_group_owners, "owner1,owner2")
        self.assertEqual(collector.gitlab_group_maintainers, "maintainer1,maintainer2")
        self.assertEqual(collector.gitlab_group_developers, "developer1,developer2")

    def test_gitlab_options(self):
        """Test setting Gitlab options from options."""
        collector = Collector(
            gitlab_url="https://gitlab.custom-domain.com",
            gitlab_token="input-G1tl4b_Tok3n!",
            gitlab_namespace_path="inputnamespacepath",
            gitlab_group_slug="input-gitlab-project",
            gitlab_group_owners="owner1,owner2",
            gitlab_group_maintainers="maintainer1,maintainer2",
            gitlab_group_developers="developer1,developer2",
        )
        self.assertEqual(collector.gitlab_url, "https://gitlab.custom-domain.com")
        self.assertEqual(collector.gitlab_token, "input-G1tl4b_Tok3n!")
        self.assertEqual(collector.gitlab_namespace_path, "inputnamespacepath")
        self.assertEqual(collector.gitlab_group_slug, "input-gitlab-project")
        self.assertEqual(collector.gitlab_group_owners, "owner1,owner2")
        self.assertEqual(collector.gitlab_group_maintainers, "maintainer1,maintainer2")
        self.assertEqual(collector.gitlab_group_developers, "developer1,developer2")
        collector.set_gitlab()
        self.assertEqual(collector.gitlab_url, "https://gitlab.custom-domain.com")
        self.assertEqual(collector.gitlab_token, "input-G1tl4b_Tok3n!")
        self.assertEqual(collector.gitlab_namespace_path, "inputnamespacepath")
        self.assertEqual(collector.gitlab_group_slug, "input-gitlab-project")
        self.assertEqual(collector.gitlab_group_owners, "owner1,owner2")
        self.assertEqual(collector.gitlab_group_maintainers, "maintainer1,maintainer2")
        self.assertEqual(collector.gitlab_group_developers, "developer1,developer2")

    def test_storage_default(self):
        """Test setting storage options from default."""
        collector = Collector()
        collector.set_digitalocean_spaces = mock.MagicMock()
        collector.set_aws_s3 = mock.MagicMock()
        with input("", {"hidden": "s3_accEss!"}, {"hidden": "s3_s3crEt!"}):
            collector.set_storage()
        self.assertEqual(collector.media_storage, "digitalocean-s3")
        self.assertEqual(collector.s3_access_id, "s3_accEss!")
        self.assertEqual(collector.s3_secret_key, "s3_s3crEt!")
        collector.set_digitalocean_spaces.assert_called_once()
        collector.set_aws_s3.assert_not_called()

    def test_storage_input(self):
        """Test setting storage options from input."""
        collector = Collector()
        collector.set_digitalocean_spaces = mock.MagicMock()
        collector.set_aws_s3 = mock.MagicMock()
        with input(
            "aws-s3", {"hidden": "s3_accEss!-input"}, {"hidden": "s3_s3crEt!-input"}
        ):
            collector.set_storage()
        self.assertEqual(collector.media_storage, "aws-s3")
        self.assertEqual(collector.s3_access_id, "s3_accEss!-input")
        self.assertEqual(collector.s3_secret_key, "s3_s3crEt!-input")
        collector.set_aws_s3.assert_called_once()
        collector.set_digitalocean_spaces.assert_not_called()

    def test_storage_input_local(self):
        """Test setting storage options from input."""
        collector = Collector()
        collector.set_digitalocean_spaces = mock.MagicMock()
        collector.set_aws_s3 = mock.MagicMock()
        with input(
            "local", {"hidden": "s3_accEss!-input"}, {"hidden": "s3_s3crEt!-input"}
        ):
            collector.set_storage()
        self.assertEqual(collector.media_storage, "local")
        self.assertEqual(collector.s3_access_id, "s3_accEss!-input")
        self.assertEqual(collector.s3_secret_key, "s3_s3crEt!-input")
        collector.set_aws_s3.assert_not_called()
        collector.set_digitalocean_spaces.assert_not_called()

    def test_storage_options(self):
        """Test setting storage options from options."""
        collector = Collector(
            media_storage="aws-s3",
            s3_access_id="s3_accEss!-options",
            s3_secret_key="s3_s3crEt!-options",
        )
        self.assertEqual(collector.media_storage, "aws-s3")
        self.assertEqual(collector.s3_access_id, "s3_accEss!-options")
        self.assertEqual(collector.s3_secret_key, "s3_s3crEt!-options")
        collector.set_digitalocean_spaces = mock.MagicMock()
        collector.set_aws_s3 = mock.MagicMock()
        with input("2", "s3_accEss-input", "s3_s3crEt!-input"):
            collector.set_storage()
        self.assertEqual(collector.media_storage, "aws-s3")
        self.assertEqual(collector.s3_access_id, "s3_accEss!-options")
        self.assertEqual(collector.s3_secret_key, "s3_s3crEt!-options")
        collector.set_aws_s3.assert_called_once()
        collector.set_digitalocean_spaces.assert_not_called()

    def test_digitalocean_spaces_input(self):
        """Test setting digitalocean spaces from input."""
        collector = Collector()
        self.assertIsNone(collector.digitalocean_token)
        self.assertIsNone(collector.s3_region)
        self.assertIsNone(collector.s3_host)
        self.assertIsNone(collector.s3_bucket_name)
        collector.set_digitalocean_token = mock.MagicMock()
        with input({"hidden": "VeRy_s3cr3t!1"}, "region"):
            collector.set_digitalocean_spaces()
        self.assertEqual(collector.digitalocean_token, "VeRy_s3cr3t!1")
        self.assertEqual(collector.s3_region, "region")
        self.assertEqual(collector.s3_host, "digitaloceanspaces.com")
        self.assertEqual(collector.s3_bucket_name, "")

    def test_digitalocean_spaces_default(self):
        """Test setting digitalocean spaces from default."""
        collector = Collector()
        self.assertIsNone(collector.digitalocean_token)
        self.assertIsNone(collector.s3_region)
        self.assertIsNone(collector.s3_host)
        self.assertIsNone(collector.s3_bucket_name)
        collector.set_digitalocean_token = mock.MagicMock()
        with input({"hidden": "VeRy_s3cr3t!1"}, ""):
            collector.set_digitalocean_spaces()
        self.assertEqual(collector.digitalocean_token, "VeRy_s3cr3t!1")
        self.assertEqual(collector.s3_region, "fra1")
        self.assertEqual(collector.s3_host, "digitaloceanspaces.com")
        self.assertEqual(collector.s3_bucket_name, "")

    def test_digitalocean_spaces_options(self):
        """Test setting digitalocean spaces from options."""
        collector = Collector(
            digitalocean_token="T0k3n!2-options", s3_region="options-region"
        )
        self.assertIsNone(collector.s3_host)
        self.assertIsNone(collector.s3_bucket_name)
        self.assertEqual(collector.digitalocean_token, "T0k3n!2-options")
        self.assertEqual(collector.s3_region, "options-region")
        collector.set_digitalocean_token = mock.MagicMock()
        collector.set_digitalocean_spaces()
        self.assertEqual(collector.digitalocean_token, "T0k3n!2-options")
        self.assertEqual(collector.s3_region, "options-region")
        self.assertEqual(collector.s3_host, "digitaloceanspaces.com")
        self.assertEqual(collector.s3_bucket_name, "")

    def test_aws_s3_default(self):
        """Test setting AWS s3 from default."""
        collector = Collector()
        self.assertIsNone(collector.s3_bucket_name)
        self.assertIsNone(collector.s3_host)
        self.assertIsNone(collector.s3_region)
        with input("", "bucket_name"):
            collector.set_aws_s3()
        self.assertEqual(collector.s3_region, "eu-central-1")
        self.assertEqual(collector.s3_host, "")
        self.assertEqual(collector.s3_bucket_name, "bucket_name")

    def test_aws_s3_input(self):
        """Test setting AWS s3 from input."""
        collector = Collector()
        self.assertIsNone(collector.s3_bucket_name)
        self.assertIsNone(collector.s3_host)
        self.assertIsNone(collector.s3_region)
        with input("custom-region", "bucket_name-input"):
            collector.set_aws_s3()
        self.assertEqual(collector.s3_region, "custom-region")
        self.assertEqual(collector.s3_host, "")
        self.assertEqual(collector.s3_bucket_name, "bucket_name-input")

    def test_aws_s3_options(self):
        """Test setting AWS s3 from options."""
        collector = Collector(s3_bucket_name="options-name", s3_region="options-region")
        self.assertIsNone(collector.s3_host)
        self.assertEqual(collector.s3_bucket_name, "options-name")
        self.assertEqual(collector.s3_region, "options-region")
        collector.set_aws_s3()
        self.assertEqual(collector.s3_host, "")
        self.assertEqual(collector.s3_region, "options-region")
        self.assertEqual(collector.s3_bucket_name, "options-name")

    def test_launch_runner(self):
        """Test launching the runner."""
        collector = Collector()
        runner = mock.MagicMock()
        collector.get_runner = mock.MagicMock(return_value=runner)
        collector.launch_runner()
        runner.run.assert_called_once()

    def test_get_runner(self):
        """Test getting the runner."""
        collector = Collector(
            backend_type="django",
            deployment_type="digitalocean-k8s",
            environments_distribution="1",
            frontend_type="nextjs",
            media_storage="local",
            project_dirname="project_dirname",
            project_name="Test Project",
            project_slug="test-project",
            project_url_dev="https://dev.test.com",
            project_url_prod="https://www.test.com",
            project_url_stage="https://stage.test.com",
            terraform_backend="terraform-cloud",
            use_redis=False,
        )
        collector._service_dir = Path(".")
        runner = collector.get_runner()
        self.assertEqual(runner.backend_type, "django")
        self.assertEqual(runner.deployment_type, "digitalocean-k8s")
        self.assertEqual(runner.environments_distribution, "1")
        self.assertEqual(runner.frontend_type, "nextjs")
        self.assertEqual(runner.media_storage, "local")
        self.assertEqual(runner.project_dirname, "project_dirname")
        self.assertEqual(runner.project_name, "Test Project")
        self.assertEqual(runner.project_slug, "test-project")
        self.assertEqual(runner.project_url_dev, "https://dev.test.com")
        self.assertEqual(runner.project_url_prod, "https://www.test.com")
        self.assertEqual(runner.project_url_stage, "https://stage.test.com")
        self.assertEqual(runner.terraform_backend, "terraform-cloud")
        self.assertEqual(runner.use_redis, False)

    def test_collect(self):
        """Test collect options."""
        collector = Collector()
        collector.set_project_name = mock.MagicMock()
        collector.set_project_slug = mock.MagicMock()
        collector.set_project_dirname = mock.MagicMock()
        collector.set_service_dir = mock.MagicMock()
        collector.set_backend_service = mock.MagicMock()
        collector.set_frontend_service = mock.MagicMock()
        collector.set_use_redis = mock.MagicMock()
        collector.set_terraform = mock.MagicMock()
        collector.set_vault = mock.MagicMock()
        collector.set_deployment_type = mock.MagicMock()
        collector.set_environments_distribution = mock.MagicMock()
        collector.set_domain_and_urls = mock.MagicMock()
        collector.set_letsencrypt = mock.MagicMock()
        collector.set_deployment = mock.MagicMock()
        collector.set_sentry = mock.MagicMock()
        collector.set_pact = mock.MagicMock()
        collector.set_gitlab = mock.MagicMock()
        collector.set_storage = mock.MagicMock()
        collector.collect()
        collector.set_project_name.assert_called_once()
        collector.set_project_slug.assert_called_once()
        collector.set_project_dirname.assert_called_once()
        collector.set_service_dir.assert_called_once()
        collector.set_backend_service.assert_called_once()
        collector.set_frontend_service.assert_called_once()
        collector.set_use_redis.assert_called_once()
        collector.set_terraform.assert_called_once()
        collector.set_vault.assert_called_once()
        collector.set_deployment_type.assert_called_once()
        collector.set_environments_distribution.assert_called_once()
        collector.set_domain_and_urls.assert_called_once()
        collector.set_letsencrypt.assert_called_once()
        collector.set_deployment.assert_called_once()
        collector.set_sentry.assert_called_once()
        collector.set_pact.assert_called_once()
        collector.set_gitlab.assert_called_once()
        collector.set_storage.assert_called_once()
