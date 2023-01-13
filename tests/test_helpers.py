"""Bootstrap helpers tests."""
import json, os, copy
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from bootstrap.helpers import CollectorJSONEncoder, format_gitlab_variable, format_tfvar, dump_options, load_options
from bootstrap.constants import DUMPS_DIR
from freezegun import freeze_time
from time import time
from tests.test_utils import mock_input

class GitlabVariableTestcase(TestCase):
    """Test the 'format_gitlab_varialbe' function."""

    def test_gitlab_variable_unmasked_unprotected(self):
        """Test the formatting of a gitlab unmasked, unprotected variable."""
        self.assertEqual(
            format_gitlab_variable("value", False, False),
            '{ value = "value", protected = false }',
        )

    def test_gitlab_variable_masked_unprotected(self):
        """Test the formatting of a gitlab masked, unprotected variable."""
        self.assertEqual(
            format_gitlab_variable("value", True, False),
            '{ value = "value", masked = true, protected = false }',
        )

    def test_gitlab_variable_unmasked_protected(self):
        """Test the formatting of a gitlab unmasked, protected variable."""
        self.assertEqual(
            format_gitlab_variable("value", False, True), '{ value = "value" }'
        )

    def test_gitlab_variable_masked_protected(self):
        """Test the formatting of a gitlab masked, unprotected variable."""
        self.assertEqual(
            format_gitlab_variable("value", True, True),
            '{ value = "value", masked = true }',
        )


class FormatTFVarTestCase(TestCase):
    """Test the 'format_tfvar' function."""

    def test_format_list(self):
        """Test the function formats a list properly."""
        self.assertEqual(format_tfvar([1, 2, 3], "list"), '["1", "2", "3"]')

    def test_format_bool(self):
        """Test the function formats a boolean properly."""
        self.assertEqual(format_tfvar(True, "bool"), "true")

    def test_format_number(self):
        """Test the function formats a number properly."""
        self.assertEqual(format_tfvar(6, "num"), "6")

    def test_format_default(self):
        """Test the function formats a boolean properly."""
        self.assertEqual(format_tfvar("something else", "default"), '"something else"')


class JSONEncoderTestCase(TestCase):
    """Test the JSONEncoder class."""
    def test_path(self):
        """Test the custon JSONEncoder with a Path."""
        self.assertEqual(
            json.dumps({"a": Path(__file__)}, cls=CollectorJSONEncoder),
            '{"a": "/app/tests/test_helpers.py"}',
        )

    def test_not_path(self):
        """Test the custon JSONEncoder without a Path."""
        self.assertEqual(
            json.dumps({"a": 3}, cls=CollectorJSONEncoder),
            '{"a": 3}',
        )

@freeze_time("2022-01-13 14:00:00")
class DumpOptionsTestCase(TestCase):
    """Test the 'dump_options' function."""

    def setUp(self) -> None:
        self.dump_path = DUMPS_DIR / f"{time():.0f}.json"
        return super().setUp()

    def test_dump_options_no(self):
        """Test not dumping the options."""
        with mock_input("n"):
            dump_options({"option":"1"})
        self.assertFalse(os.path.exists(self.dump_path))

    def test_dump_options_yes(self):
        """Test not dumping the options."""
        data_to_dump = {"option":"1"}
        with mock_input("y"):
            dump_options(data_to_dump)
        try:
            self.assertTrue(os.path.exists(self.dump_path))
            dumped_data = json.load(open(self.dump_path))
            self.assertEqual(dumped_data,data_to_dump)
        finally:
            os.remove(self.dump_path)


# class LoadOptionsTestCase(TestCase):
#     """Test the 'load_options' function."""

#     # def setUp(self) -> None:
#     #     """ """
#     #     self.original_dumps_dir = copy.deepcopy(DUMPS_DIR)
#     #     return super().setUp()
    
#     # def tearDown(self) -> None:
#     #     """ """
#     #     DUMPS_DIR = self.original_dumps_dir
#     #     return super().tearDown()

#     def test_load_options(self):
#         """Test options are loaded."""
#         with mock_input("y"):
#             breakpoint()
#             self.assertEqual(load_options(), {"option":2})
