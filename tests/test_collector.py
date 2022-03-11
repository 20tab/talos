"""Project bootstrap tests."""

from contextlib import contextmanager
from io import StringIO
from unittest import TestCase, mock

from bootstrap.collector import (
    clean_backend_sentry_dsn,
    clean_backend_service_slug,
    clean_backend_type,
    clean_deployment_type,
    clean_digitalocean_clusters_data,
    clean_digitalocean_media_storage_data,
    clean_environment_distribution,
    clean_frontend_sentry_dsn,
    clean_frontend_service_slug,
    clean_frontend_type,
    clean_gitlab_group_data,
    clean_media_storage,
    clean_pact_broker_data,
    clean_project_domain,
    clean_project_slug,
    clean_project_urls,
    clean_sentry_org,
    clean_service_dir,
    clean_use_gitlab,
    clean_use_pact,
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

    @mock.patch("pathlib.Path.is_absolute", return_value=True)
    def test_clean_service_dir(self, m):
        """Test cleaning the service directory."""
        self.assertTrue(
            clean_service_dir("tests", "my_project").endswith("/tests/my_project")
        )
        with mock.patch("shutil.rmtree", return_value=None), mock.patch(
            "pathlib.Path.is_dir", return_value=True
        ), input("Y"):
            self.assertTrue(
                clean_service_dir("tests", "my_project").endswith("/tests/my_project")
            )

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
            self.assertEqual(clean_deployment_type(None), "k8s-digitalocean")
        with input("non-existing", ""):
            self.assertEqual(clean_deployment_type(None), "k8s-digitalocean")

    def test_clean_environment_distribution(self):
        """Test cleaning the environment distribution."""
        with input("1", ""):
            self.assertEqual(clean_environment_distribution(None), "1")
        with input("999", "3"):
            self.assertEqual(clean_environment_distribution(None), "3")

    def test_clean_project_domain(self):
        """Test cleaning the project domain."""
        with input("myproject.com"):
            self.assertEqual(clean_project_domain("myproject.com"), "myproject.com")

    def test_clean_project_urls(self):
        """Test cleaning the project URLs."""
        # project domain set
        with input("alpha", "beta", "www2"):
            self.assertEqual(
                clean_project_urls(
                    "my-project", "myproject.com", "", "", "", "", "", ""
                ),
                (
                    "alpha",
                    "beta",
                    "www2",
                    "https://alpha.myproject.com",
                    "https://beta.myproject.com",
                    "https://www2.myproject.com",
                ),
            )
        self.assertEqual(
            clean_project_urls(
                "my-project", "myproject.com", "alpha", "beta", "www2", "", "", ""
            ),
            (
                "alpha",
                "beta",
                "www2",
                "https://alpha.myproject.com",
                "https://beta.myproject.com",
                "https://www2.myproject.com",
            ),
        )
        # project domain not set
        with input(
            "https://alpha.myproject.com/",
            "https://beta.myproject.com/",
            "https://www2.myproject.com/",
        ):
            self.assertEqual(
                clean_project_urls("my-project", "", "", "", "", "", "", ""),
                (
                    "",
                    "",
                    "",
                    "https://alpha.myproject.com",
                    "https://beta.myproject.com",
                    "https://www2.myproject.com",
                ),
            )
        self.assertEqual(
            clean_project_urls(
                "my-project",
                "",
                "",
                "",
                "",
                "https://alpha.myproject.com/",
                "https://beta.myproject.com/",
                "https://www2.myproject.com/",
            ),
            (
                "",
                "",
                "",
                "https://alpha.myproject.com",
                "https://beta.myproject.com",
                "https://www2.myproject.com",
            ),
        )

    def test_clean_sentry_org(self):
        """Test cleaning the Sentry organization."""
        self.assertEqual(clean_sentry_org("My Project"), "My Project")
        with input("My Project"):
            self.assertEqual(clean_sentry_org(None), "My Project")

    def test_clean_backend_sentry_dsn(self):
        """Test cleaning the backend Sentry DSN."""
        self.assertIsNone(clean_backend_sentry_dsn(None, None))
        with input("https://public@sentry.example.com/1"):
            self.assertEqual(
                clean_backend_sentry_dsn(
                    "django", "https://public@sentry.example.com/1"
                ),
                "https://public@sentry.example.com/1",
            )

    def test_clean_frontend_sentry_dsn(self):
        """Test cleaning the frontend Sentry DSN."""
        self.assertIsNone(clean_frontend_sentry_dsn(None, None))
        with input("https://public@sentry.example.com/1"):
            self.assertEqual(
                clean_frontend_sentry_dsn(
                    "django", "https://public@sentry.example.com/1"
                ),
                "https://public@sentry.example.com/1",
            )

    def test_clean_cluster_data(self):
        """Test cleaning the cluster data."""
        self.assertEqual(
            clean_digitalocean_clusters_data(
                "nyc1", "nyc1", "db-s-8vcpu-16gb", "nyc1", "db-s-8vcpu-16gb", True
            ),
            ("nyc1", "nyc1", "db-s-8vcpu-16gb", "nyc1", "db-s-8vcpu-16gb", True),
        )
        self.assertEqual(
            clean_digitalocean_clusters_data(
                "nyc1", "nyc1", "db-s-8vcpu-16gb", None, None, False
            ),
            ("nyc1", "nyc1", "db-s-8vcpu-16gb", None, None, False),
        )
        with input("nyc1", "nyc1", "db-s-8vcpu-16gb", "Y", "nyc1", "db-s-8vcpu-16gb"):
            self.assertEqual(
                clean_digitalocean_clusters_data(None, None, None, None, None, None),
                ("nyc1", "nyc1", "db-s-8vcpu-16gb", "nyc1", "db-s-8vcpu-16gb", True),
            )

    def test_clean_use_pact(self):
        """Test telling whether Pact should be configured."""
        with input("n"):
            self.assertFalse(clean_use_pact(None))

    def test_clean_broker_data(self):
        """Test cleaning the broker data."""
        self.assertEqual(
            clean_pact_broker_data(
                "https://broker.myproject.com", "user.name", "mYV4l1DP4sSw0rD"
            ),
            ("https://broker.myproject.com", "user.name", "mYV4l1DP4sSw0rD"),
        )
        with input(
            "https://broker.myproject.com", "user.name", {"hidden": "mYV4l1DP4sSw0rD"}
        ):
            self.assertEqual(
                clean_pact_broker_data("", "", ""),
                ("https://broker.myproject.com", "user.name", "mYV4l1DP4sSw0rD"),
            )

    def test_clean_media_storage(self):
        """Test cleaning the media storage."""
        with input("local"):
            self.assertEqual(clean_media_storage(""), "local")

    def test_clean_use_gitlab(self):
        """Test telling whether Gitlab should be used."""
        with input("n"):
            self.assertFalse(clean_use_gitlab(None))

    def test_clean_gitlab_group_data(self):
        """Test cleaning the Gitlab group data."""
        with input("", "Y"):
            self.assertEqual(
                clean_gitlab_group_data(
                    "my-project",
                    "",
                    "mYV4l1DT0k3N",
                    "owner, owner.other",
                    "maintainer, maintainer.other",
                    "developer, developer.other",
                ),
                (
                    "my-project",
                    "mYV4l1DT0k3N",
                    "owner, owner.other",
                    "maintainer, maintainer.other",
                    "developer, developer.other",
                ),
            )
        with input("Y"):
            self.assertEqual(
                clean_gitlab_group_data(
                    "",
                    "my-project-group",
                    "mYV4l1DT0k3N",
                    "owner, owner.other",
                    "maintainer, maintainer.other",
                    "developer, developer.other",
                ),
                (
                    "my-project-group",
                    "mYV4l1DT0k3N",
                    "owner, owner.other",
                    "maintainer, maintainer.other",
                    "developer, developer.other",
                ),
            )
        with input(
            "my-project-group",
            "Y",
            {"hidden": "mYV4l1DT0k3N"},
            "owner, owner.other",
            "maintainer, maintainer.other",
            "developer, developer.other",
        ):
            self.assertEqual(
                clean_gitlab_group_data("", "", "", "", "", ""),
                ("my-project-group", "mYV4l1DT0k3N", "", "", ""),
            )

    def test_clean_digitalocean_media_storage_data(self):
        """Test cleaning the DigitalOcean media storage data."""
        self.assertEqual(
            clean_digitalocean_media_storage_data(
                "mYV4l1DT0k3N", "nyc1", "mYV4l1D1D", "mYV4l1Ds3cR3tK3y"
            ),
            ("mYV4l1DT0k3N", "nyc1", "mYV4l1D1D", "mYV4l1Ds3cR3tK3y"),
        )
        with input(
            {"hidden": "mYV4l1DT0k3N"},
            "nyc1",
            {"hidden": "mYV4l1D1D"},
            {"hidden": "mYV4l1Ds3cR3tK3y"},
        ):
            self.assertEqual(
                clean_digitalocean_media_storage_data("", "", "", ""),
                ("mYV4l1DT0k3N", "nyc1", "mYV4l1D1D", "mYV4l1Ds3cR3tK3y"),
            )
