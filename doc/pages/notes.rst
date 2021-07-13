notes
*****

rst
---

A quick primer on ``rst``
https://docutils.sourceforge.io/docs/user/rst/quickref.html


Office documents
----------------

Office documents are converted using the helper functions found in
``src/os2datascanner/engine2/model/derived/libreoffice.py``

An office document is converted to HTML using ``libreoffice`` invoked from
the CLI. If some of the resulting HTML files are larger than ``size_treshold``,
specified in the config file under ``[model.libreoffice]``, the html is replaced
with a simpler representation.

The HTML is further converted to the representation needed by the rule being
applied. This is done by the more generic convertes found in the
``src/os2datascanner/engine2/conversions`` folder
