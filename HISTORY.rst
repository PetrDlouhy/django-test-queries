.. :changelog:

History
-------

0.4.0 (TBD)
++++++++++++++++++

* Remove Django Debug Toolbar dependency - use Django's built-in query capture
* Improve reliability and performance of query recording
* Maintain 100% backward compatibility

0.3.0 (2024-05-16)
++++++++++++++++++

* output messages to the error report and replace Django SQL output
* sort queries before diffing
* store stacktrace and other information in .sqllog.full_record file

0.2.2 (2023-08-26)
++++++++++++++++++

* Real fix for DDT 3.8.1

0.2.1 (2023-08-24)
++++++++++++++++++

* Remove DDT version requirements


0.2.0 (2023-08-15)
++++++++++++++++++

* Fixes for new version of DDT (tested in 3.8.1 - 4.2.0)
* Automatic testing

0.1.0 (2023-04-21)
++++++++++++++++++

* First release on PyPI.
