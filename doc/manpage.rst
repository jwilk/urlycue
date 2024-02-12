=======
urlycue
=======

------------------------
command-line URL checker
------------------------

:manual section: 1
:version: urlycue 0.3.4
:date: 2024-02-12

Synopsis
--------
**urlycue** [*option*...] [*file*...]

Description
-----------

**urlycue** extracts URLs from the specified files
(or from stdin) and tries to retrieve them.
It reports retrieval errors and permanent redirects.

Options
-------

-h, --help
   Show help message and exit.
--version
   Show version information and exit.
--list
   List all extracted URLs without checking anything.
-v, --verbose
   Print also URLs without issues.
-k, --no-cert-check
   Don't verify server certificates.

Example
-------

::

   $ urlycue doc/README
   doc/README:7: [301 Moved Permanently] http://github.com/jwilk/urlycue.git -> https://github.com/jwilk/urlycue
   doc/README:8: [404 Not Found] http://example.org/nonexistent

.. vim:ts=3 sts=3 sw=3
