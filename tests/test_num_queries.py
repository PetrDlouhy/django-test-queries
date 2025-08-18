import os

from django.db import connections
from django.test import TestCase

from test_queries import NumQueriesMixin

current_directory = os.getcwd()


class TestNumQueriesMixin(NumQueriesMixin, TestCase):
    def setUp(self):
        os.environ["TEST_QUERIES_REWRITE_SQLLOGS"] = "False"

    def test_basic_functionality(self):
        with self.assertNumQueries(1):
            connections["default"].cursor().execute("SELECT 1")

    def test_file_creation(self):
        # This test checks if the SQL log file is created
        expected_filename = "path_to_expected_file.sqllog"  # Adjust this
        with self.assertNumQueries(1):
            connections["default"].cursor().execute("SELECT 1")
        self.assertTrue(os.path.exists(expected_filename))

    def test_file_comparison(self):
        # This test checks if the SQL log files are compared correctly
        expected_filename = "path_to_expected_file.sqllog"  # Adjust this
        with open(expected_filename, "w") as f:
            f.write("SELECT 1")
        with self.assertNumQueries(1):
            connections["default"].cursor().execute("SELECT 1")

    def test_file_comparison_function(self):
        expected_filename = "path_to_expected_file.sqllog"  # Adjust this
        with open(expected_filename, "w") as f:
            f.write("SELECT 1")

        def call_sql():
            connections["default"].cursor().execute("SELECT 1")

        self.assertNumQueries(1, call_sql)

    def test_environment_variables(self):
        """If TEST_QUERIES_DISABLE=True, all values should pass."""
        os.environ["TEST_QUERIES_DISABLE"] = "1"
        with self.assertNumQueries(100):
            connections["default"].cursor().execute("SELECT 1")
        os.environ["TEST_QUERIES_DISABLE"] = "0"
        # But if TEST_QUERIES_DISABLE=False, it should fail
        with self.assertRaisesRegex(AssertionError, "1 != 100 : 1 queries executed, 100 expected"):
            with self.assertNumQueries(100):
                connections["default"].cursor().execute("SELECT 1")

    def test_file_comparison_with_existing_lines(self):
        # This test checks if the SQL log files are compared correctly when the file already has lines
        expected_filename = (
            "tests/sqllog/test_num_queries.TestNumQueriesMixin.test_file_comparison_with_existing_lines.0.sqllog"
        )
        os.makedirs(os.path.dirname(expected_filename), exist_ok=True)
        with open(expected_filename, "w") as f:
            f.write("SELECT 1\nSELECT 2")  # Writing multiple lines to the file
        with self.assertNumQueries(2):
            connections["default"].cursor().execute("SELECT 1")
            connections["default"].cursor().execute("SELECT 2")

    def test_file_comparison_with_existing_lines_not_equal(self):
        expected_filename = (
            "tests/sqllog/"
            "test_num_queries.TestNumQueriesMixin.test_file_comparison_with_existing_lines_not_equal.0.sqllog"
        )
        os.makedirs(os.path.dirname(expected_filename), exist_ok=True)
        with open(expected_filename, "w") as f:
            f.write("SELECT 2")  # Writing multiple lines to the file
        with self.assertRaises(AssertionError) as cm:
            with self.assertNumQueries(1):
                connections["default"].cursor().execute("SELECT 1")
                connections["default"].cursor().execute("SELECT 2")
        error_message = str(cm.exception)
        self.assertIn("2 != 1 : 2 queries executed, 1 expected", error_message)
        self.assertIn("New query was recorded:\n\tSELECT 1", error_message)
        self.assertIn("See difference:", error_message)
        self.assertIn(
            f"diff {current_directory}/tests/sqllog/test_num_queries."
            "TestNumQueriesMixin.test_file_comparison_with_existing_lines_not_equal.0.sqllog "
            f"{current_directory}/tests/sqllog/test_num_queries."
            "TestNumQueriesMixin.test_file_comparison_with_existing_lines_not_equal.0.sqllog.new",
            error_message,
        )

    def test_file_comparison_with_existing_lines_delete(self):
        expected_filename = (
            "tests/sqllog/test_num_queries."
            "TestNumQueriesMixin.test_file_comparison_with_existing_lines_delete.0.sqllog"
        )
        os.makedirs(os.path.dirname(expected_filename), exist_ok=True)
        with open(expected_filename, "w") as f:
            f.write("SELECT 1\nSELECT 3\nSELECT 3")  # Writing multiple lines to the file
        with self.assertRaises(AssertionError) as cm:
            with self.assertNumQueries(1):
                connections["default"].cursor().execute("SELECT 1")
                connections["default"].cursor().execute("SELECT 2")
                connections["default"].cursor().execute("SELECT 3")
        error_message = str(cm.exception)
        self.assertIn("3 != 1 : 3 queries executed, 1 expected", error_message)
        self.assertIn("New query was recorded:\n\tSELECT 2", error_message)
        self.assertIn("See difference:", error_message)
        self.assertIn(
            f"diff {current_directory}/tests/sqllog/test_num_queries."
            "TestNumQueriesMixin.test_file_comparison_with_existing_lines_delete.0.sqllog "
            f"{current_directory}/tests/sqllog/test_num_queries."
            "TestNumQueriesMixin.test_file_comparison_with_existing_lines_delete.0.sqllog.new",
            error_message,
        )
        self.assertIn("delete    a[2:3] --> b[3:3] ['SELECT 3...'] --> []", error_message)

    def test_file_comparison_with_existing_lines_replace(self):
        expected_filename = (
            "tests/sqllog/test_num_queries."
            "TestNumQueriesMixin.test_file_comparison_with_existing_lines_replace.0.sqllog"
        )
        os.makedirs(os.path.dirname(expected_filename), exist_ok=True)
        with open(expected_filename, "w") as f:
            f.write("SELECT 1\nSELECT 2\nSELECT 3\nSELECT 5\nSELECT 6")  # Writing multiple lines to the file
        with self.assertRaises(AssertionError) as cm:
            with self.assertNumQueries(1):
                connections["default"].cursor().execute("SELECT 1")
                connections["default"].cursor().execute("SELECT 2")
                connections["default"].cursor().execute("SELECT 4")
                connections["default"].cursor().execute("SELECT 5")
                connections["default"].cursor().execute("SELECT 6")
        error_message = str(cm.exception)
        self.assertIn("5 != 1 : 5 queries executed, 1 expected", error_message)
        self.assertIn("Query was replaced:\n\tSELECT 4", error_message)
        self.assertIn("See difference:", error_message)
        self.assertIn(
            f"diff {current_directory}/tests/sqllog/test_num_queries."
            "TestNumQueriesMixin.test_file_comparison_with_existing_lines_replace.0.sqllog "
            f"{current_directory}/tests/sqllog/test_num_queries."
            "TestNumQueriesMixin.test_file_comparison_with_existing_lines_replace.0.sqllog.new",
            error_message,
        )

    def test_fallback_for_missing_file_attribute(self):
        """Test the fallback path when module.__file__ is None."""
        # Create a mock test instance where the module has no __file__ attribute
        import inspect
        import types

        # Create a fake module without __file__
        fake_module = types.ModuleType("fake_test_module")
        # Don't set __file__ attribute - it will be None

        # Temporarily replace the module
        original_getmodule = inspect.getmodule

        def mock_getmodule(obj):
            return fake_module

        inspect.getmodule = mock_getmodule

        try:
            # This should use the fallback path
            with self.assertNumQueries(1):
                connections["default"].cursor().execute("SELECT 1")

            # Check that the fallback path was used
            self.assertIn("test_file", self.context["filename"])

        finally:
            # Restore original function
            inspect.getmodule = original_getmodule
