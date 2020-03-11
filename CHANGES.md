Change log for Hold It!
=======================

Version 1.1.4
-------------

* In the documentation, mention the need for the Tind account to have access to Tind Global Lists


Version 1.1.3
-------------

* Fix a bug in the Windows installer script where it used the wrong `.exe` file name
* Make the uninstallation process use the windows "Add or remove programs" system utility instead of using the `unins000.exe` program in the _Hold It!_ folder


Version 1.1.2
-------------

* Fix a critical bug in how Shibboleth authentication with Tind.io is handled.  It is a bit of a mystery to me how the previous code could have worked (and worked in production, no less).


Version 1.1.1
-------------

* Try harder to rename a previous Word document if one exists
* Try to detect if the Word doc is open in another application


Version 1.1.0
-------------

* At the request of the circulation desk, make it include books marked as "lost" in addition to those marked "on shelf", because apparently patrons sometimes put holds on lost books
* Fix bug in algorithm that computes differences in the new requests versus past requests in the Google spreadsheet
* Fix the Word template to use Arial, a font actually available on Windows (unlike what I had used before)
* Rename from _Holdit!_ to _Hold It!_, because it's better that way
* Minor changes under the hood involving Google authentication
