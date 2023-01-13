"""Test utils for the project."""


from contextlib import contextmanager
from io import StringIO
from unittest import mock


@contextmanager
def mock_input(*cmds):
    """Mock the user input."""
    visible_cmds = "\n".join(c for c in cmds if isinstance(c, str))
    hidden_cmds = [c["hidden"] for c in cmds if isinstance(c, dict) and "hidden" in c]
    with mock.patch("sys.stdin", StringIO(f"{visible_cmds}\n")), mock.patch(
        "getpass.getpass", side_effect=hidden_cmds
    ):
        yield
