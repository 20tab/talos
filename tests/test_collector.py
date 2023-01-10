"""Project bootstrap tests."""

from contextlib import contextmanager
from io import StringIO
from pathlib import Path
from unittest import TestCase, mock

from bootstrap.collector import Collector


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

    # def test_clean_kubernetes_credentials(self):
    #     """Test cleaning the Kubernetes credentials."""
    #     certificate_path = Path(__file__).parent / "__init__.py"
    #     with input(
    #         str(certificate_path),
    #         "https://kube.com:16443",
    #         {"hidden": "K8sT0k3n"},
    #     ):
    #         self.assertEqual(
    #             clean_kubernetes_credentials(None, None, None),
    #             (str(certificate_path), "https://kube.com:16443", "K8sT0k3n"),
    #         )
    #     with input(
    #         str(certificate_path),
    #         {"hidden": "K8sT0k3n"},
    #     ):
    #         self.assertEqual(
    #             clean_kubernetes_credentials(None, "https://kube.com:16443", None),
    #             (str(certificate_path), "https://kube.com:16443", "K8sT0k3n"),
    #         )

    # def test_clean_other_k8s_options(self):
    #     """Test cleaning the Kubernetes database."""
    #     self.assertEqual(
    #         clean_other_k8s_options(
    #             "postgres:14", "10Gi", None, "/etc/k8s-volume-data", None, False
    #         ),
    #         ("postgres:14", "10Gi", "", "/etc/k8s-volume-data", ""),
    #     )
    #     self.assertEqual(
    #         clean_other_k8s_options(
    #             "postgres:14", "10Gi", None, "/etc/k8s-volume-data", "redis:6.2", True
    #         ),
    #         ("postgres:14", "10Gi", "", "/etc/k8s-volume-data", "redis:6.2"),
    #     )
    #     with input(
    #         "redis:6",
    #     ):
    #         self.assertEqual(
    #             clean_other_k8s_options(
    #                 "postgres:14", "10Gi", None, "/etc/k8s-volume-data", None, True
    #             ),
    #             ("postgres:14", "10Gi", "", "/etc/k8s-volume-data", "redis:6"),
    #         )

    # def test_clean_sentry_org(self):
    #     """Test cleaning the Sentry organization."""
    #     self.assertEqual(clean_sentry_org("My Project"), "My Project")
    #     with input("My Project"):
    #         self.assertEqual(clean_sentry_org(None), "My Project")

    # def test_clean_sentry_dsn(self):
    #     """Test cleaning the Sentry DSN of a service."""
    #     self.assertIsNone(clean_sentry_dsn(None, None))
    #     with input(""):
    #         self.assertEqual(clean_sentry_dsn("backend", None), "")
    #     with input("bad-dsn-url", "https://public@sentry.example.com/1"):
    #         self.assertEqual(
    #             clean_sentry_dsn("backend", None), "https://public@sentry.example.com/1"
    #         )
    #     with input("https://public@sentry.example.com/1"):
    #         self.assertEqual(
    #             clean_sentry_dsn("backend", None), "https://public@sentry.example.com/1"
    #         )

    # def test_clean_sentry_data(self):
    #     """Test cleaning the Sentry data."""
    #     self.assertEqual(
    #         clean_sentry_data(
    #             "test-company",
    #             "https://sentry.io",
    #             "my-sentry-t0K3N",
    #             None,
    #             "https://sentry.io/backend-dsn",
    #             None,
    #             "https://sentry.io/frontend-dsn",
    #         ),
    #         (None, None, None, None, None),
    #     )
    #     self.assertEqual(
    #         clean_sentry_data(
    #             "test-company",
    #             "https://sentry.io",
    #             "my-sentry-t0K3N",
    #             "backend",
    #             "https://sentry.io/backend-dsn",
    #             "frontend",
    #             "https://sentry.io/frontend-dsn",
    #         ),
    #         (
    #             "test-company",
    #             "https://sentry.io",
    #             "my-sentry-t0K3N",
    #             "https://sentry.io/backend-dsn",
    #             "https://sentry.io/frontend-dsn",
    #         ),
    #     )
    #     with input("y", "my-company"):
    #         self.assertEqual(
    #             clean_sentry_data(
    #                 None,
    #                 "https://sentry.io",
    #                 "my-sentry-t0K3N",
    #                 "backend",
    #                 "https://sentry.io/backend-dsn",
    #                 "frontend",
    #                 "https://sentry.io/frontend-dsn",
    #             ),
    #             (
    #                 "my-company",
    #                 "https://sentry.io",
    #                 "my-sentry-t0K3N",
    #                 "https://sentry.io/backend-dsn",
    #                 "https://sentry.io/frontend-dsn",
    #             ),
    #         )

    # def test_clean_digitalocean_options(self):
    #     """Test cleaning the DigitalOcean options."""
    #     self.assertEqual(
    #         clean_digitalocean_options(
    #             True,
    #             False,
    #             "nyc1",
    #             "nyc1",
    #             "db-s-8vcpu-16gb",
    #             None,
    #             None,
    #             False,
    #         ),
    #         (True, False, "nyc1", "nyc1", "db-s-8vcpu-16gb", None, None),
    #     )
    #     with input(
    #         "y", "n", "nyc1", "nyc1", "db-s-8vcpu-16gb", "nyc1", "db-s-8vcpu-16gb"
    #     ):
    #         self.assertEqual(
    #             clean_digitalocean_options(
    #                 None, None, None, None, None, None, None, True
    #             ),
    #             (
    #                 True,
    #                 False,
    #                 "nyc1",
    #                 "nyc1",
    #                 "db-s-8vcpu-16gb",
    #                 "nyc1",
    #                 "db-s-8vcpu-16gb",
    #             ),
    #         )

    # def test_clean_broker_data(self):
    #     """Test cleaning the broker data."""
    #     with input("Y", "https://broker.myproject.com"):
    #         self.assertEqual(
    #             clean_pact_broker_data(None, "user.name", "mYV4l1DP4sSw0rD"),
    #             ("https://broker.myproject.com", "user.name", "mYV4l1DP4sSw0rD"),
    #         )
    #     with input(
    #         "user.name",
    #         {"hidden": "mYV4l1DP4sSw0rD"},
    #     ):
    #         self.assertEqual(
    #             clean_pact_broker_data("https://broker.myproject.com", None, None),
    #             ("https://broker.myproject.com", "user.name", "mYV4l1DP4sSw0rD"),
    #         )
    #     self.assertEqual(clean_pact_broker_data("", None, None), (None, None, None))

    # def test_clean_media_storage(self):
    #     """Test cleaning the media storage."""
    #     with input("local"):
    #         self.assertEqual(clean_media_storage(""), "local")

    # def test_clean_gitlab_data(self):
    #     """Test cleaning the GitLab group data."""
    #     with input("Y"):
    #         self.assertEqual(
    #             clean_gitlab_data(
    #                 "my-project",
    #                 "https://gitlab.com/",
    #                 "mYV4l1DT0k3N",
    #                 "test/namespace/path",
    #                 "my-gitlab-group",
    #                 "owner, owner.other",
    #                 "maintainer, maintainer.other",
    #                 "developer, developer.other",
    #             ),
    #             (
    #                 "https://gitlab.com",
    #                 "mYV4l1DT0k3N",
    #                 "test/namespace/path",
    #                 "my-gitlab-group",
    #                 "owner, owner.other",
    #                 "maintainer, maintainer.other",
    #                 "developer, developer.other",
    #             ),
    #         )
    #     with input(
    #         "Y",
    #         "",
    #         "/non-valid#path/BAD&/",
    #         "_my/valid/path/",
    #         "my-gitlab-group",
    #     ):
    #         self.assertEqual(
    #             clean_gitlab_data(
    #                 "my-project",
    #                 None,
    #                 "mYV4l1DT0k3N",
    #                 None,
    #                 None,
    #                 "owner, owner.other",
    #                 "maintainer, maintainer.other",
    #                 "developer, developer.other",
    #             ),
    #             (
    #                 "https://gitlab.com",
    #                 "mYV4l1DT0k3N",
    #                 "_my/valid/path",
    #                 "my-gitlab-group",
    #                 "owner, owner.other",
    #                 "maintainer, maintainer.other",
    #                 "developer, developer.other",
    #             ),
    #         )
    #     with input(
    #         "Y",
    #         "https://my-custom-gitlab.com/",
    #         {"hidden": "mYV4l1DT0k3N"},
    #         "/non-valid#path/BAD&/",
    #         "",
    #         "my-gitlab-group",
    #         "owner, owner.other",
    #         "maintainer, maintainer.other",
    #         "developer, developer.other",
    #     ):
    #         self.assertEqual(
    #             clean_gitlab_data(
    #                 "my-project", None, None, None, None, None, None, None
    #             ),
    #             (
    #                 "https://my-custom-gitlab.com",
    #                 "mYV4l1DT0k3N",
    #                 "",
    #                 "my-gitlab-group",
    #                 "owner, owner.other",
    #                 "maintainer, maintainer.other",
    #                 "developer, developer.other",
    #             ),
    #         )
    #     with input(
    #         "Y",
    #         "https://gitlab.com/",
    #         {"hidden": "mYV4l1DT0k3N"},
    #         "",
    #         "my-gitlab-group",
    #         "Y",
    #         "owner, owner.other",
    #         "maintainer, maintainer.other",
    #         "developer, developer.other",
    #     ):
    #         self.assertEqual(
    #             clean_gitlab_data(
    #                 "my-project", None, None, None, None, None, None, None
    #             ),
    #             (
    #                 "https://gitlab.com",
    #                 "mYV4l1DT0k3N",
    #                 "",
    #                 "my-gitlab-group",
    #                 "owner, owner.other",
    #                 "maintainer, maintainer.other",
    #                 "developer, developer.other",
    #             ),
    #         )
    #     self.assertEqual(
    #         clean_gitlab_data("my-project", "", "", "", "", "", "", ""),
    #         (None, None, None, None, None, None, None),
    #     )

    # def test_clean_s3_media_storage_data(self):
    #     """Test cleaning the S3 media storage data."""
    #     self.assertEqual(
    #         clean_s3_media_storage_data(
    #             "digitalocean-s3",
    #             "mYV4l1DT0k3N",
    #             "nyc1",
    #             None,
    #             "mYV4l1D1D",
    #             "mYV4l1Ds3cR3tK3y",
    #             None,
    #         ),
    #         (
    #             "mYV4l1DT0k3N",
    #             "nyc1",
    #             "digitaloceanspaces.com",
    #             "mYV4l1D1D",
    #             "mYV4l1Ds3cR3tK3y",
    #             "",
    #         ),
    #     )
    #     with input(
    #         {"hidden": "mYV4l1DT0k3N"},
    #         "nyc1",
    #         {"hidden": "mYV4l1D1D"},
    #         {"hidden": "mYV4l1Ds3cR3tK3y"},
    #     ):
    #         self.assertEqual(
    #             clean_s3_media_storage_data(
    #                 "digitalocean-s3", None, None, None, None, None, None
    #             ),
    #             (
    #                 "mYV4l1DT0k3N",
    #                 "nyc1",
    #                 "digitaloceanspaces.com",
    #                 "mYV4l1D1D",
    #                 "mYV4l1Ds3cR3tK3y",
    #                 "",
    #             ),
    #         )
    #     self.assertEqual(
    #         clean_s3_media_storage_data(
    #             "aws-s3",
    #             None,
    #             "eu-central-1",
    #             None,
    #             "mYV4l1D1D",
    #             "mYV4l1Ds3cR3tK3y",
    #             "mybucket",
    #         ),
    #         (
    #             "",
    #             "eu-central-1",
    #             "",
    #             "mYV4l1D1D",
    #             "mYV4l1Ds3cR3tK3y",
    #             "mybucket",
    #         ),
    #     )
    #     with input(
    #         "eu-central-1",
    #         {"hidden": "mYV4l1D1D"},
    #         {"hidden": "mYV4l1Ds3cR3tK3y"},
    #         "mybucket",
    #     ):
    #         self.assertEqual(
    #             clean_s3_media_storage_data(
    #                 "aws-s3", None, None, None, None, None, None
    #             ),
    #             ("", "eu-central-1", "", "mYV4l1D1D", "mYV4l1Ds3cR3tK3y", "mybucket"),
    #         )
