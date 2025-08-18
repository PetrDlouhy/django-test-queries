import inspect
import os
import re
from difflib import SequenceMatcher
from typing import Any, Dict

from django.db import DEFAULT_DB_ALIAS, connections
from django.test import TransactionTestCase
from django.test.testcases import _AssertNumQueriesContext


def strtobool(val):
    """Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    if val in ("n", "no", "f", "false", "off", "0"):
        return False
    raise ValueError(f"invalid truth value {val}")


def boolean_env_var(var: str, default=False) -> bool:
    return strtobool(os.environ.get(var, str(default)))


def write_full_record(records, file):
    """Write detailed query records to file."""
    for error_dict in records:
        file.write(f"Raw SQL: {error_dict['raw_sql']}\n\n")
        file.write("Stacktrace:\n")
        stacktrace_entries = [
            f'  File: "{s[0]}", Line: {s[1]}, in {s[2]}\n    {s[3]}' for s in error_dict["stacktrace"]
        ]
        file.write("\n".join(stacktrace_entries) + "\n")

        file.write("\n")
        for rk, rv in error_dict.items():
            if rk in ["sql", "params"]:
                file.write(f"{rk}: {rv}\n\n")
        file.write("\n")
        file.write("----------------------------------------------------------------------")
        file.write("\n")
        file.write("\n")


class _AssertQueriesContext(_AssertNumQueriesContext):
    """Enhanced query context that captures and compares SQL queries."""

    def __init__(self, test_case, num, connection, context_dict):
        self.context_dict = context_dict
        super().__init__(test_case, num, connection)

    def __exit__(self, exc_type, exc_value, traceback):
        if boolean_env_var("TEST_QUERIES_DISABLE"):
            return

        # Populate records from Django's captured queries
        self._populate_records()

        try:
            super_result = super().__exit__(exc_type, exc_value, traceback)
            return super_result
        except AssertionError as e:
            custom_query_message = self._format_query_comparison()
            custom_message = "\n".join(e.args[0].split("\n")[0:1]) + "\n" + custom_query_message
            raise AssertionError(custom_message) from None

    def _populate_records(self):
        """Convert Django's captured queries to our record format."""
        for query in self.captured_queries:
            self.context_dict["records"].append(
                {
                    "sql": query["sql"],
                    "raw_sql": re.sub(r'SAVEPOINT ".*"', 'SAVEPOINT "%1"', query["sql"]),
                    "stacktrace": [],
                    "args": (),
                    "time": query.get("time", "0"),
                }
            )

    def _format_query_comparison(self):
        """Format query comparison output showing differences."""
        formatted_queries = []
        filename = self.context_dict["filename"]

        # Read existing queries from file
        try:
            with open(filename, "r") as f:
                existing_lines = [line.strip() for line in f.readlines()]
        except FileNotFoundError:
            existing_lines = []

        # Get current queries
        current_queries = [s["raw_sql"] for s in self.context_dict["records"]]

        # Compare queries if we have existing ones
        if existing_lines:
            existing_lines.sort()
            current_queries_sorted = current_queries.copy()
            current_queries_sorted.sort()

            s = SequenceMatcher(None, existing_lines, current_queries_sorted)
            for tag, i1, i2, j1, j2 in s.get_opcodes():
                if tag not in ["insert", "replace", "equal"]:
                    formatted_queries.append(
                        "{:7}   a[{}:{}] --> b[{}:{}] {!r:>8} --> {!r}".format(
                            tag,
                            i1,
                            i2,
                            j1,
                            j2,
                            [s[:50] + "..." for s in existing_lines[i1:i2]],
                            [s[:50] + "..." for s in current_queries_sorted[j1:j2]],
                        )
                    )
                if tag in ["insert", "replace"]:
                    for j in range(j1, j2):
                        if tag == "insert":
                            formatted_queries.append("New query was recorded:")
                        elif tag == "replace":
                            formatted_queries.append("Query was replaced:")
                        formatted_queries.append("\t" + current_queries_sorted[j] + "\n")

        # Write output files
        self._write_output_files(filename, current_queries, formatted_queries)

        return "\n".join(formatted_queries)

    def _write_output_files(self, filename, current_queries, formatted_queries):
        """Write query log files and comparison output."""
        # Ensure directory exists
        os.makedirs(filename.rsplit("/", 1)[0], exist_ok=True)

        # Write full record file
        fr_filename = filename + ".full_record"
        with open(fr_filename, "w") as f:
            write_full_record(self.context_dict["records"], f)
        formatted_queries.append(f"  full record: {fr_filename}")

        # Write query log file
        output_filename = filename
        if not boolean_env_var("TEST_QUERIES_REWRITE_SQLLOGS"):
            output_filename += ".new"

        with open(output_filename, "w") as f:
            f.write("\n".join(current_queries) + "\n")

        # Add diff information
        formatted_queries.append("See difference:")
        formatted_queries.append(f"  diff {filename} {output_filename}")


class NumQueriesMixin(TransactionTestCase):
    """Mixin that provides enhanced assertNumQueries with SQL logging and comparison."""

    executed_times = 0
    context: Dict[str, Any] = {}

    def assertNumQueries(self, num, func=None, *args, using=DEFAULT_DB_ALIAS, **kwargs):  # noqa: N802
        """Assert the number of queries executed and log them for comparison."""
        conn = connections[using]

        # Generate filename for SQL log
        module = inspect.getmodule(self)
        if module and hasattr(module, "__file__") and module.__file__:
            path, file_prefix = module.__file__[:-3].rsplit("/", 1)
        else:
            # Fallback for tests without proper __file__ attribute
            path = "."
            file_prefix = "test_file"

        filename = (
            f"{path}/sqllog/{file_prefix}."
            f"{self.__class__.__name__}."
            f"{self._testMethodName}.{self.executed_times}.sqllog"
        )
        self.executed_times += 1

        # Initialize context
        self.context["filename"] = filename
        self.context["records"] = []

        # Create enhanced context (no DDT dependency needed)
        context = _AssertQueriesContext(self, num, conn, self.context)

        if func is None:
            return context

        with context:
            func(*args, **kwargs)
