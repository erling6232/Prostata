#############
Auto-prostate
#############

|coverage|
|Docs Badge|

|pypi| |pyversions| |downloads| |buildstatus|


Auto-prostate is a python project to build prostate pipeline analysing MR prostate studies.

Configuration file
------------------

.. code-block:: console

    [pacs]
    host=server.local
    port=104
    aet=PACS
    studydescription="*Prostate*"

    [store]
    cmove=LOCALAET

    [mysql]
    database=
    host=
    user=
    password=

Programs
--------

initialize-database
~~~~~~~~~~~~~~~~~~~

Initialize the database for auto-prostate.

* initialize-database -c configfile

scan-pacs
~~~~~~~~~

Scan the PACS system to detect newly arrived studies.

* scan-pacs -c configfile

Data store
----------

Table studies
~~~~~~~~~~~~~

+------------+---------------------------+----------+
| Column     | Description               | Type     |
+============+===========================+==========+
| stuinsuid  | Study Instance UID        | varchar  |
+------------+---------------------------+----------+
| studyid    | Study ID                  | varchar  |
+------------+---------------------------+----------+
| studydate  | Study Date                | varchar  |
+------------+---------------------------+----------+
| studytime  | Study Time                | varchar  |
+------------+---------------------------+----------+
| studydescr | Study Description         | varchar  |
+------------+---------------------------+----------+
| bodypartex | Body Part Examined        | varchar  |
+------------+---------------------------+----------+
| accno      | Accession Number          | varchar  |
+------------+---------------------------+----------+
| status     | Status Code               | varchar  |
+------------+---------------------------+----------+
| series     | No. of Series Received    | int      |
+------------+---------------------------+----------+
| images     | No. of Images Received    | int      |
+------------+---------------------------+----------+

Status codes
~~~~~~~~~~~~

+-------------+---------------------------------+
| Code        | Description                     |
+=============+=================================+
| detected    | First images receive in PACS    |
+-------------+---------------------------------+
| stable      | Stable number of images in PACS |
+-------------+---------------------------------+
| cmoved      | Transfer from PACS initiated    |
+-------------+---------------------------------+




.. |Docs Badge| image:: https://readthedocs.org/projects/auto-prostate/badge/
    :alt: Documentation Status
    :scale: 100%
    :target: https://auto-prostate.readthedocs.io

.. |buildstatus| image:: https://github.com/erling6232/auto-prostate/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/erling6232/auto-prostate/actions?query=branch%3Amaster
    :alt: Build Status

.. _buildstatus: https://github.com/erling6232/auto-prostate/actions

.. |coverage| image:: https://codecov.io/gh/erling6232/auto-prostate/branch/master/graph/badge.svg?token=GT9KZV2TWT
    :alt: Coverage
    :target: https://codecov.io/gh/erling6232/auto-prostate

.. |pypi| image:: https://img.shields.io/pypi/v/auto-prostate.svg
    :target: https://pypi.python.org/pypi/auto-prostate
    :alt: PyPI Version

.. |pyversions| image:: https://img.shields.io/pypi/pyversions/auto-prostate.svg
   :target: https://pypi.python.org/pypi/auto-prostate/
   :alt: Supported Python Versions

.. |downloads| image:: https://img.shields.io/pypi/dm/auto-prostate?color=blue
   :alt: PyPI Downloads
