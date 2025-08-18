=============================
Django test queries
=============================

.. image:: https://badge.fury.io/py/dj-test-queries.svg
    :target: https://badge.fury.io/py/dj-test-queries

.. image:: https://codecov.io/gh/PetrDlouhy/django-test-queries/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/PetrDlouhy/django-test-queries

Extension of assertNumQueries that can record queries that were executed and show the differences in future runs.
It also shows traceback of where the query was called.

**🚀 NEW: DDT-Free Implementation** - No longer requires django-debug-toolbar! More reliable and faster query capture using Django's built-in functionality.

Documentation
-------------

The full documentation is at https://dj-test-queries.readthedocs.io.

Quickstart
----------

Install ``dj-test-queries``:

.. code-block:: bash

   pip install dj-test-queries

Apply ``NumQueriesMixin`` to your test and use ``assertNumQueries`` as you would normally do:

.. code-block:: python

    from test_queries import NumQueriesMixin

    class XYZTests(NumQueriesMixin, TestCase):
        def test_xyz(self):
            with self.assertNumQueries(3):
                xyz()

Generating SQL log records
--------------------------

Run the tests with ``TEST_QUERIES_REWRITE_SQLLOGS`` environment variable to generate sqllog files:

.. code-block:: bash

    TEST_QUERIES_REWRITE_SQLLOGS="true" manage.py test

Files like ``test_views.XYZTests.test_xyz.sqllog`` will appear in ``sqllog`` directory next to your ``test_views.py`` file.

If you will run the test next time and the queries will differ from previous, the test will print out output detailing the change with stacktrace from where the query was executed.
You can also enlist the ``*.sqllog`` files to your repository to see the changes.

If the tests are executed without the ``TEST_QUERIES_REWRITE_SQLLOGS`` environment variable, the logs are created to files named like ``test_views.XYZTests.test_xyz.sqllog`` to make possible to compare the difference.

Running Tests
-------------

Does the code actually work?

::

    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ pip install tox
    (myenv) $ tox


Development commands
---------------------

::

    pip install -r requirements_dev.txt
    invoke -l


Credits
-------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-djangopackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-djangopackage`: https://github.com/pydanny/cookiecutter-djangopackage
