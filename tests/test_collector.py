"""Project bootstrap tests."""

from contextlib import contextmanager
from io import StringIO
from pathlib import Path
from unittest import TestCase, mock

from bootstrap.collector import (
    clean_backend_service_slug,
    clean_backend_type,
    clean_deployment_type,
    clean_digitalocean_options,
    clean_domains,
    clean_environment_distribution,
    clean_frontend_service_slug,
    clean_frontend_type,
    clean_gitlab_data,
    clean_kubernetes_credentials,
    clean_media_storage,
    clean_other_k8s_options,
    clean_pact_broker_data,
    clean_project_slug,
    clean_s3_media_storage_data,
    clean_sentry_data,
    clean_sentry_dsn,
    clean_sentry_org,
    clean_service_dir,
    clean_terraform_backend,
    clean_vault_data,
)


@contextmanager
def input(*cmds):
    """Mock the input."""
    visible_cmds = "\n".join([c for c in cmds if isinstance(c, str)])
    hidden_cmds = [c.get("hidden") for c in cmds if isinstance(c, dict)]
    with mock.patch("sys.stdin", StringIO(f"{visible_cmds}\n")), mock.patch(
        "getpass.getpass", side_effect=hidden_cmds
    ):
        yield


class TestBootstrapCollector(TestCase):
    """Test the bootstrap collector."""

    maxDiff = None

    def test_clean_project_slug(self):
        """Test cleaning the project slug."""
        with input("My Project"):
            self.assertEqual(clean_project_slug("My Project", None), "my-project")
        project_slug = "my-new-project"
        self.assertEqual(
            clean_project_slug("My Project", "my-new-project"), project_slug
        )

    def test_clean_service_dir(self):
        """Test cleaning the service directory."""
        MockedPath = mock.MagicMock(spec=Path)
        output_dir = MockedPath("mocked-tests")
        output_dir.is_absolute.return_value = True
        service_dir = MockedPath("mocked-tests/my_project")
        service_dir.is_dir.return_value = False
        output_dir.__truediv__.return_value = service_dir
        self.assertEqual(clean_service_dir(output_dir, "my_project"), service_dir)
        service_dir.is_dir.return_value = True
        output_dir.__truediv__.return_value = service_dir
        with mock.patch("bootstrap.collector.rmtree", return_value=None), input("Y"):
            self.assertEqual(clean_service_dir(output_dir, "my_project"), service_dir)

    def test_clean_backend_type(self):
        """Test cleaning the back end type."""
        self.assertEqual(clean_backend_type("django"), "django")
        with input("non-existing", ""):
            self.assertEqual(clean_backend_type("non-existing"), "django")

    def test_clean_backend_service_slug(self):
        """Test cleaning the back end service slug."""
        with input(""):
            self.assertEqual(clean_backend_service_slug(""), "backend")
        with input("my backend"):
            self.assertEqual(clean_backend_service_slug(""), "mybackend")

    def test_clean_frontend_type(self):
        """Test cleaning the front end type."""
        with input(""):
            self.assertEqual(clean_frontend_type(""), "nextjs")
        with input("non-existing", ""):
            self.assertEqual(clean_frontend_type(""), "nextjs")

    def test_clean_frontend_service_slug(self):
        """Test cleaning the front end service slug."""
        with input(""):
            self.assertEqual(clean_frontend_service_slug(None), "frontend")
        with input("my frontend"):
            self.assertEqual(clean_frontend_service_slug(None), "myfrontend")

    def test_clean_deployment_type(self):
        """Test cleaning the deployment type."""
        with input(""):
            self.assertEqual(clean_deployment_type(None), "digitalocean-k8s")
        with input("non-existing", ""):
            self.assertEqual(clean_deployment_type(None), "digitalocean-k8s")

    def test_clean_terraform_backend(self):
        """Test cleaning the Terraform ."""
        self.assertEqual(
            clean_terraform_backend("gitlab", None, None, None, None, None),
            ("gitlab", None, None, None, None, None),
        )
        with input("gitlab"):
            self.assertEqual(
                clean_terraform_backend("wrong-backend", None, None, None, None, None),
                ("gitlab", None, None, None, None, None),
            )
        with input("terraform-cloud", "", "myOrg", "y", "bad-email", "admin@test.com"):
            self.assertEqual(
                clean_terraform_backend(
                    "wrong-backend", None, "mytfcT0k3N", None, None, None
                ),
                (
                    "terraform-cloud",
                    "app.terraform.io",
                    "mytfcT0k3N",
                    "myOrg",
                    True,
                    "admin@test.com",
                ),
            )
        with input(
            "terraform-cloud",
            "tfc.mydomain.com",
            {"hidden": "mytfcT0k3N"},
            "myOrg",
            "n",
            None,
        ):
            self.assertEqual(
                clean_terraform_backend("wrong-backend", None, None, None, None, None),
                (
                    "terraform-cloud",
                    "tfc.mydomain.com",
                    "mytfcT0k3N",
                    "myOrg",
                    False,
                    "",
                ),
            )

    def test_clean_vault_data(self):
        """Test cleaning the Vault data ."""
        self.assertEqual(
            clean_vault_data("v4UlTtok3N", "https://vault.test.com", True),
            ("v4UlTtok3N", "https://vault.test.com"),
        )
        with input("y", {"hidden": "v4UlTtok3N"}, "https://vault.test.com"):
            self.assertEqual(
                clean_vault_data(None, None, True),
                ("v4UlTtok3N", "https://vault.test.com"),
            )
        with input("y", {"hidden": "v4UlTtok3N"}, "y", "https://vault.test.com"):
            self.assertEqual(
                clean_vault_data(None, None, False),
                ("v4UlTtok3N", "https://vault.test.com"),
            )
        with input(
            "y", {"hidden": "v4UlTtok3N"}, "y", "bad_address", "https://vault.test.com"
        ):
            self.assertEqual(
                clean_vault_data(None, None, False),
                ("v4UlTtok3N", "https://vault.test.com"),
            )
        with input("n"):
            self.assertEqual(clean_vault_data(None, None, True), (None, None))

    def test_clean_environment_distribution(self):
        """Test cleaning the environment distribution."""
        self.assertEqual(clean_environment_distribution(None, "other-k8s"), "1")
        with input("1", ""):
            self.assertEqual(
                clean_environment_distribution(None, "digitalocean-k8s"), "1"
            )
        with input("999", "3"):
            self.assertEqual(
                clean_environment_distribution(None, "digitalocean-k8s"), "3"
            )

    def test_clean_kubernetes_credentials(self):
        """Test cleaning the Kubernetes credentials."""
        certificate_path = Path(__file__).parent / "__init__.py"
        with input(
            str(certificate_path),
            "https://kube.com:16443",
            {"hidden": "K8sT0k3n"},
        ):
            self.assertEqual(
                clean_kubernetes_credentials(None, None, None),
                (str(certificate_path), "https://kube.com:16443", "K8sT0k3n"),
            )
        with input(
            str(certificate_path),
            {"hidden": "K8sT0k3n"},
        ):
            self.assertEqual(
                clean_kubernetes_credentials(None, "https://kube.com:16443", None),
                (str(certificate_path), "https://kube.com:16443", "K8sT0k3n"),
            )

    def test_clean_other_k8s_options(self):
        """Test cleaning the Kubernetes database."""
        self.assertEqual(
            clean_other_k8s_options(
                "postgres:14", "10Gi", None, "/etc/k8s-volume-data", None, False
            ),
            ("postgres:14", "10Gi", "", "/etc/k8s-volume-data", ""),
        )
        self.assertEqual(
            clean_other_k8s_options(
                "postgres:14", "10Gi", None, "/etc/k8s-volume-data", "redis:6.2", True
            ),
            ("postgres:14", "10Gi", "", "/etc/k8s-volume-data", "redis:6.2"),
        )
        with input(
            "redis:6",
        ):
            self.assertEqual(
                clean_other_k8s_options(
                    "postgres:14", "10Gi", None, "/etc/k8s-volume-data", None, True
                ),
                ("postgres:14", "10Gi", "", "/etc/k8s-volume-data", "redis:6"),
            )

    def test_clean_domains(self):
        """Test cleaning the project domains."""
        # project domain set
        with input("alpha", "beta", "www2"):
            self.assertEqual(
                clean_domains(
                    "projectslug",
                    "myproject.com",
                    False,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    "test@test.com",
                ),
                (
                    "myproject.com",
                    "alpha",
                    "beta",
                    "www2",
                    None,
                    "https://alpha.myproject.com",
                    "https://beta.myproject.com",
                    "https://www2.myproject.com",
                    "test@test.com",
                ),
            )
        self.assertEqual(
            clean_domains(
                "projectslug",
                "myproject.com",
                False,
                "alpha",
                "beta",
                "www2",
                None,
                None,
                None,
                None,
                "test@test.com",
            ),
            (
                "myproject.com",
                "alpha",
                "beta",
                "www2",
                None,
                "https://alpha.myproject.com",
                "https://beta.myproject.com",
                "https://www2.myproject.com",
                "test@test.com",
            ),
        )
        # project domain not set
        with input(
            "myproject.com",
            "alpha",
            "beta",
            "www2",
            "N",
        ):
            self.assertEqual(
                clean_domains(
                    "projectslug",
                    None,
                    False,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
                (
                    "myproject.com",
                    "alpha",
                    "beta",
                    "www2",
                    None,
                    "https://alpha.myproject.com",
                    "https://beta.myproject.com",
                    "https://www2.myproject.com",
                    None,
                ),
            )
        # monitoring enabled
        with input("alpha", "beta", "www2", "mylogs", "N"):
            self.assertEqual(
                clean_domains(
                    "projectslug",
                    "myproject.com",
                    True,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
                (
                    "myproject.com",
                    "alpha",
                    "beta",
                    "www2",
                    "mylogs",
                    "https://alpha.myproject.com",
                    "https://beta.myproject.com",
                    "https://www2.myproject.com",
                    None,
                ),
            )  # Let's Encrypt certificates enabled
        with input(
            "myproject.com",
            "alpha",
            "beta",
            "www2",
            "mylogs",
            "Y",
            "test@test.com",
        ):
            self.assertEqual(
                clean_domains(
                    "projectslug",
                    "",
                    True,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
                (
                    "myproject.com",
                    "alpha",
                    "beta",
                    "www2",
                    "mylogs",
                    "https://alpha.myproject.com",
                    "https://beta.myproject.com",
                    "https://www2.myproject.com",
                    "test@test.com",
                ),
            )

    def test_clean_sentry_org(self):
        """Test cleaning the Sentry organization."""
        self.assertEqual(clean_sentry_org("My Project"), "My Project")
        with input("My Project"):
            self.assertEqual(clean_sentry_org(None), "My Project")

    def test_clean_sentry_dsn(self):
        """Test cleaning the Sentry DSN of a service."""
        self.assertIsNone(clean_sentry_dsn(None, None))
        with input(""):
            self.assertEqual(clean_sentry_dsn("backend", None), "")
        with input("bad-dsn-url", "https://public@sentry.example.com/1"):
            self.assertEqual(
                clean_sentry_dsn("backend", None), "https://public@sentry.example.com/1"
            )
        with input("https://public@sentry.example.com/1"):
            self.assertEqual(
                clean_sentry_dsn("backend", None), "https://public@sentry.example.com/1"
            )

    def test_clean_sentry_data(self):
        """Test cleaning the Sentry data."""
        self.assertEqual(
            clean_sentry_data(
                "test-company",
                "https://sentry.io",
                "my-sentry-t0K3N",
                None,
                "https://sentry.io/backend-dsn",
                None,
                "https://sentry.io/frontend-dsn",
            ),
            (None, None, None, None, None),
        )
        self.assertEqual(
            clean_sentry_data(
                "test-company",
                "https://sentry.io",
                "my-sentry-t0K3N",
                "backend",
                "https://sentry.io/backend-dsn",
                "frontend",
                "https://sentry.io/frontend-dsn",
            ),
            (
                "test-company",
                "https://sentry.io",
                "my-sentry-t0K3N",
                "https://sentry.io/backend-dsn",
                "https://sentry.io/frontend-dsn",
            ),
        )
        with input("y", "my-company"):
            self.assertEqual(
                clean_sentry_data(
                    None,
                    "https://sentry.io",
                    "my-sentry-t0K3N",
                    "backend",
                    "https://sentry.io/backend-dsn",
                    "frontend",
                    "https://sentry.io/frontend-dsn",
                ),
                (
                    "my-company",
                    "https://sentry.io",
                    "my-sentry-t0K3N",
                    "https://sentry.io/backend-dsn",
                    "https://sentry.io/frontend-dsn",
                ),
            )

    def test_clean_digitalocean_options(self):
        """Test cleaning the DigitalOcean options."""
        self.assertEqual(
            clean_digitalocean_options(
                True,
                False,
                "nyc1",
                "nyc1",
                "db-s-8vcpu-16gb",
                None,
                None,
                False,
            ),
            (True, False, "nyc1", "nyc1", "db-s-8vcpu-16gb", None, None),
        )
        with input(
            "y", "n", "nyc1", "nyc1", "db-s-8vcpu-16gb", "nyc1", "db-s-8vcpu-16gb"
        ):
            self.assertEqual(
                clean_digitalocean_options(
                    None, None, None, None, None, None, None, True
                ),
                (
                    True,
                    False,
                    "nyc1",
                    "nyc1",
                    "db-s-8vcpu-16gb",
                    "nyc1",
                    "db-s-8vcpu-16gb",
                ),
            )

    def test_clean_broker_data(self):
        """Test cleaning the broker data."""
        with input("Y", "https://broker.myproject.com"):
            self.assertEqual(
                clean_pact_broker_data(None, "user.name", "mYV4l1DP4sSw0rD"),
                ("https://broker.myproject.com", "user.name", "mYV4l1DP4sSw0rD"),
            )
        with input(
            "user.name",
            {"hidden": "mYV4l1DP4sSw0rD"},
        ):
            self.assertEqual(
                clean_pact_broker_data("https://broker.myproject.com", None, None),
                ("https://broker.myproject.com", "user.name", "mYV4l1DP4sSw0rD"),
            )
        self.assertEqual(clean_pact_broker_data("", None, None), (None, None, None))

    def test_clean_media_storage(self):
        """Test cleaning the media storage."""
        with input("local"):
            self.assertEqual(clean_media_storage(""), "local")

    def test_clean_gitlab_data(self):
        """Test cleaning the GitLab group data."""
        with input("Y"):
            self.assertEqual(
                clean_gitlab_data(
                    "my-project",
                    "https://gitlab.com/",
                    "mYV4l1DT0k3N",
                    "test/namespace/path",
                    "my-gitlab-group",
                    "owner, owner.other",
                    "maintainer, maintainer.other",
                    "developer, developer.other",
                ),
                (
                    "https://gitlab.com",
                    "mYV4l1DT0k3N",
                    "test/namespace/path",
                    "my-gitlab-group",
                    "owner, owner.other",
                    "maintainer, maintainer.other",
                    "developer, developer.other",
                ),
            )
        with input(
            "Y",
            "",
            "/non-valid#path/BAD&/",
            "_my/valid/path/",
            "my-gitlab-group",
        ):
            self.assertEqual(
                clean_gitlab_data(
                    "my-project",
                    None,
                    "mYV4l1DT0k3N",
                    None,
                    None,
                    "owner, owner.other",
                    "maintainer, maintainer.other",
                    "developer, developer.other",
                ),
                (
                    "https://gitlab.com",
                    "mYV4l1DT0k3N",
                    "_my/valid/path",
                    "my-gitlab-group",
                    "owner, owner.other",
                    "maintainer, maintainer.other",
                    "developer, developer.other",
                ),
            )
        with input(
            "Y",
            "https://my-custom-gitlab.com/",
            {"hidden": "mYV4l1DT0k3N"},
            "/non-valid#path/BAD&/",
            "",
            "my-gitlab-group",
            "owner, owner.other",
            "maintainer, maintainer.other",
            "developer, developer.other",
        ):
            self.assertEqual(
                clean_gitlab_data(
                    "my-project", None, None, None, None, None, None, None
                ),
                (
                    "https://my-custom-gitlab.com",
                    "mYV4l1DT0k3N",
                    "",
                    "my-gitlab-group",
                    "owner, owner.other",
                    "maintainer, maintainer.other",
                    "developer, developer.other",
                ),
            )
        with input(
            "Y",
            "https://gitlab.com/",
            {"hidden": "mYV4l1DT0k3N"},
            "",
            "my-gitlab-group",
            "Y",
            "owner, owner.other",
            "maintainer, maintainer.other",
            "developer, developer.other",
        ):
            self.assertEqual(
                clean_gitlab_data(
                    "my-project", None, None, None, None, None, None, None
                ),
                (
                    "https://gitlab.com",
                    "mYV4l1DT0k3N",
                    "",
                    "my-gitlab-group",
                    "owner, owner.other",
                    "maintainer, maintainer.other",
                    "developer, developer.other",
                ),
            )
        self.assertEqual(
            clean_gitlab_data("my-project", "", "", "", "", "", "", ""),
            (None, None, None, None, None, None, None),
        )

    def test_clean_s3_media_storage_data(self):
        """Test cleaning the S3 media storage data."""
        self.assertEqual(
            clean_s3_media_storage_data(
                "digitalocean-s3",
                "mYV4l1DT0k3N",
                "nyc1",
                None,
                "mYV4l1D1D",
                "mYV4l1Ds3cR3tK3y",
                None,
            ),
            (
                "mYV4l1DT0k3N",
                "nyc1",
                "digitaloceanspaces.com",
                "mYV4l1D1D",
                "mYV4l1Ds3cR3tK3y",
                "",
            ),
        )
        with input(
            {"hidden": "mYV4l1DT0k3N"},
            "nyc1",
            {"hidden": "mYV4l1D1D"},
            {"hidden": "mYV4l1Ds3cR3tK3y"},
        ):
            self.assertEqual(
                clean_s3_media_storage_data(
                    "digitalocean-s3", None, None, None, None, None, None
                ),
                (
                    "mYV4l1DT0k3N",
                    "nyc1",
                    "digitaloceanspaces.com",
                    "mYV4l1D1D",
                    "mYV4l1Ds3cR3tK3y",
                    "",
                ),
            )
        self.assertEqual(
            clean_s3_media_storage_data(
                "aws-s3",
                None,
                "eu-central-1",
                None,
                "mYV4l1D1D",
                "mYV4l1Ds3cR3tK3y",
                "mybucket",
            ),
            (
                "",
                "eu-central-1",
                "",
                "mYV4l1D1D",
                "mYV4l1Ds3cR3tK3y",
                "mybucket",
            ),
        )
        with input(
            "eu-central-1",
            {"hidden": "mYV4l1D1D"},
            {"hidden": "mYV4l1Ds3cR3tK3y"},
            "mybucket",
        ):
            self.assertEqual(
                clean_s3_media_storage_data(
                    "aws-s3", None, None, None, None, None, None
                ),
                ("", "eu-central-1", "", "mYV4l1D1D", "mYV4l1Ds3cR3tK3y", "mybucket"),
            )
