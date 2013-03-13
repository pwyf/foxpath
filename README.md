FoXPath
=======

Authors: Ben Webb, Mark Brough, Martin Keegan

FoXPath is a toy wrapper language for XPath1.0, for those who don't want
to use XQuery.

This code is currently AGPL as it was initially developed as part of a
vertically-integrated web app; the current maintainers are investigating
rewriting, or getting the right to relicense, the AGPL-covered part such
that it may be more readily be used in a library; the affected code is
the version of foxpath/mapping.py checked in in the first commit to github.

Supported formats
=================

* X exists?
* X exists more than N times?
* X or X exists?
* only one of X or X exists?
* X is an T?
* X has more than N characters?
* X sum to N?
* X is in list L?

Where:
* L is the name of a list (e.g. a codelist)
* N is a number
* T is a type
* X is an XPath string
