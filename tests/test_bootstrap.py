"""Project bootstrap tests."""

import os
from contextlib import contextmanager
from io import StringIO
from unittest import TestCase, mock

from bootstrap.options import (
    get_backend_service_slug,
    get_backend_type,
    get_broker_data,
    get_cluster_data,
    get_deployment_type,
    get_digitalocean_media_storage_data,
    get_digitalocean_token,
    get_environment_distribution,
    get_frontend_service_slug,
    get_frontend_type,
    get_gitlab_group_data,
    get_is_digitalocean_enabled,
    get_media_storage,
    get_output_dir,
    get_project_dirname,
    get_project_domain,
    get_project_slug,
    get_project_urls,
    get_sentry_org,
    get_sentry_token,
    get_sentry_url,
    get_service_dir,
    get_service_slug,
    get_use_gitlab,
    get_use_pact,
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


class TestBootstrapOptions(TestCase):
    """Test the bootstrap options."""

    maxDiff = None

    def test_get_output_dir(self):
        """Test returning the output directory."""
        with mock.patch.dict(os.environ, {"OUTPUT_DIR": "my dir"}):
            self.assertEqual(get_output_dir(), "my dir")
        self.assertEqual(get_output_dir("my other dir"), "my other dir")

    def test_get_project_slug(self):
        """Test returning the project slug."""
        with input("My Project"):
            self.assertEqual(get_project_slug("My Project", None), "my-project")
        project_slug = "my-new-project"
        self.assertEqual(get_project_slug("My Project", "my-new-project"), project_slug)

    def test_get_project_dirname(self):
        """Test returning the project directory name."""
        self.assertEqual(get_project_dirname("my-project"), "myproject")

    def test_get_service_slug(self):
        """Test returning the service slug."""
        self.assertEqual(get_service_slug(), "orchestrator")

    @mock.patch("pathlib.Path.is_absolute", return_value=True)
    def test_get_service_dir(self, m):
        """Test returning the service directory."""
        self.assertEqual(get_service_dir("tests", "my_project"), "/tests/my_project")
        with mock.patch("shutil.rmtree", return_value=None), mock.patch(
            "pathlib.Path.is_dir", return_value=True
        ), input("Y"):
            self.assertEqual(
                get_service_dir("tests", "my_project"), "/tests/my_project"
            )

    def test_get_backend_type(self):
        """Test returning the back end type."""
        self.assertEqual(get_backend_type("django"), "django")
        with input("non-existing", ""):
            self.assertEqual(get_backend_type("non-existing"), "django")

    def test_get_backend_service_slug(self):
        """Test returning the back end service slug."""
        self.assertEqual(get_backend_service_slug(), None)
        with input(""):
            self.assertEqual(get_backend_service_slug(backend_type="django"), "backend")
        with input("my backend"):
            self.assertEqual(
                get_backend_service_slug(backend_type="django"), "mybackend"
            )

    def test_get_frontend_type(self):
        """Test returning the front end type."""
        with input(""):
            self.assertEqual(get_frontend_type(), "nextjs")
        with input("non-existing", ""):
            self.assertEqual(get_frontend_type(), "nextjs")

    def test_get_frontend_service_slug(self):
        """Test returning the front end service slug."""
        self.assertEqual(get_frontend_service_slug(), None)
        with input(""):
            self.assertEqual(
                get_frontend_service_slug(frontend_type="nextjs"), "frontend"
            )
        with input("my frontend"):
            self.assertEqual(
                get_frontend_service_slug(frontend_type="nextjs"), "myfrontend"
            )

    def test_get_deployment_type(self):
        """Test returning the deployment type."""
        with input(""):
            self.assertEqual(get_deployment_type(), "k8s-digitalocean")
        with input("non-existing", ""):
            self.assertEqual(get_deployment_type(), "k8s-digitalocean")

    def test_is_digitalocean_enabled(self):
        """Test telling whether DigitalOcean should be enabled."""
        self.assertTrue(get_is_digitalocean_enabled("k8s-digitalocean"))
        self.assertFalse(get_is_digitalocean_enabled("non-existing"))

    def test_get_digitalocean_token(self):
        """Test returning the DigitalOcean token."""
        with input("mYV4l1DT0k3N"):
            self.assertEqual(get_digitalocean_token("mYV4l1DT0k3N"), "mYV4l1DT0k3N")

    def test_get_environment_distribution(self):
        """Test returning the environment distribution."""
        with input("1", ""):
            self.assertEqual(get_environment_distribution(), "1")
        with input("999", "3"):
            self.assertEqual(get_environment_distribution(), "3")

    def test_get_project_domain(self):
        """Test returning the project domain."""
        with input("myproject.com"):
            self.assertEqual(get_project_domain("myproject.com"), "myproject.com")

    def test_get_project_urls(self):
        """Test returning the project URLs."""
        # project domain set
        with input("alpha", "beta", "www2"):
            self.assertEqual(
                get_project_urls("my-project", "myproject.com"),
                (
                    "myproject.com",
                    "https://alpha.myproject.com",
                    "https://beta.myproject.com",
                    "https://www2.myproject.com",
                ),
            )
        self.assertEqual(
            get_project_urls("my-project", "myproject.com", "alpha", "beta", "www2"),
            (
                "myproject.com",
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
                get_project_urls("my-project", None),
                (
                    "",
                    "https://alpha.myproject.com",
                    "https://beta.myproject.com",
                    "https://www2.myproject.com",
                ),
            )
        self.assertEqual(
            get_project_urls(
                "my-project",
                None,
                None,
                None,
                None,
                "https://alpha.myproject.com/",
                "https://beta.myproject.com/",
                "https://www2.myproject.com/",
            ),
            (
                "",
                "https://alpha.myproject.com",
                "https://beta.myproject.com",
                "https://www2.myproject.com",
            ),
        )

    def test_get_sentry_org(self):
        """Test returning the Sentry organization."""
        self.assertEqual(get_sentry_org("My Project"), "My Project")
        with input("My Project"):
            self.assertEqual(get_sentry_org(), "My Project")

    def test_get_cluster_data(self):
        """Test returning the cluster data."""
        self.assertEqual(
            get_cluster_data("nyc1", "nyc1", "db-s-8vcpu-16gb"),
            ("nyc1", "nyc1", "db-s-8vcpu-16gb"),
        )
        with input("nyc1", "nyc1", "db-s-8vcpu-16gb"):
            self.assertEqual(get_cluster_data(), ("nyc1", "nyc1", "db-s-8vcpu-16gb"))

    def test_get_sentry_url(self):
        """Test returning the Sentry URL."""
        self.assertEqual(
            get_sentry_url("https://myproject.com"), "https://myproject.com"
        )
        with input("https://myproject.com"):
            self.assertEqual(
                get_sentry_url("https://myproject.com"), "https://myproject.com"
            )

    def test_get_sentry_token(self):
        """Test returning the Sentry token."""
        with input("mYV4l1DT0k3N"):
            self.assertEqual(get_sentry_token("mYV4l1DT0k3N"), "mYV4l1DT0k3N")

    def test_get_use_pact(self):
        """Test telling whether Pact should be configured."""
        with input("n"):
            self.assertFalse(get_use_pact())

    def test_get_broker_data(self):
        """Test returning the broker data."""
        self.assertEqual(
            get_broker_data(
                "https://broker.myproject.com", "user.name", "mYV4l1DP4sSw0rD"
            ),
            ("https://broker.myproject.com", "user.name", "mYV4l1DP4sSw0rD"),
        )
        with input(
            "https://broker.myproject.com", "user.name", {"hidden": "mYV4l1DP4sSw0rD"}
        ):
            self.assertEqual(
                get_broker_data(),
                ("https://broker.myproject.com", "user.name", "mYV4l1DP4sSw0rD"),
            )

    def test_get_media_storage(self):
        """Test returning the media storage."""
        with input("local"):
            self.assertEqual(get_media_storage(), "local")

    def test_get_use_gitlab(self):
        """Test telling whether Gitlab should be used."""
        with input("n"):
            self.assertFalse(get_use_gitlab())

    def test_get_gitlab_group_data(self):
        """Test returning the Gitlab group data."""
        with input("", "Y"):
            self.assertEqual(
                get_gitlab_group_data(
                    "my-project",
                    None,
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
                get_gitlab_group_data(
                    None,
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
                get_gitlab_group_data(),
                (
                    "my-project-group",
                    "mYV4l1DT0k3N",
                    "owner, owner.other",
                    "maintainer, maintainer.other",
                    "developer, developer.other",
                ),
            )

    def test_get_digitalocean_media_storage_data(self):
        """Test returning the DigitalOcean media storage data."""
        self.assertEqual(
            get_digitalocean_media_storage_data(
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
                get_digitalocean_media_storage_data(),
                ("mYV4l1DT0k3N", "nyc1", "mYV4l1D1D", "mYV4l1Ds3cR3tK3y"),
            )
