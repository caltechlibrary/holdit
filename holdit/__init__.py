'''
Holdit! generates a printable Word document containing recent hold requests and
also update the relevant Google spreadsheet used for tracking requests.

The Caltech Library's Circulation Desk handles, among other things, requests
by patrons to put books or other materials on hold.  However, the catalog
management software does not have a simple way to produce a printable list of
items to hold.  The staff who go to the stacks to find materials have to look
up the information from the LIMS system used by Caltech (TIND), write the
information on paper, and update a Google spreadsheet used to track requests.

Holdit! is aimed at automating more of this procedure to reduce frustration
and possible errors.  It uses Shibboleth to log in to the Caltech Library
system, scrapes TIND to get the necessary information, produces a printable
document (based on a customizable template), and updates the Google
spreadsheet used to track holds.

The program has both a GUI interface and a command-line interface.  The GUI
interface is simple: a user starts the program in a typical way (e.g., by
double-clicking the program icon) and it asks for login credentials for
Caltech.tind.io. The image at right depicts the first dialog. After the user
types in a login name and password, and clicks the OK button, the program
does the following behind the scenes:

1. Searches Caltech.tind.io for the most recent hold requests
2. Scrapes the HTML page returned by the TIND search
3. Downloads the Google spreadsheet used by the Circulation staff
4. Compares the two data sources to determine if the TIND search returned new holds
5. Adds any new hold requests to the Google spreadsheet
6. Creates a Word document listing the latest hold requests (if any)
7. Opens the Word document so that the user can print it

Holdit! presents only one other dialog: to ask the user whether the Google
spreadsheet should be opened in a browser window.  If the user clicks the Yes
button, it's opened.  Either way, Holdit! exits after the user answers the
dialog.

The Word document created by Holdit! is based on a template Word file
unimaginatively named 'template.docx', which Holdit! looks for in the same
folder where the program is found.  Users can modify the look and content of
the template as they wish in order to customize the format of the printed
hold sheets.  Variables used in the template are indicated by surrounding
special terms with '{{' and '}}'; these then get substituted by Holdit!
when it generates the printable document.

Holdit! will write the output to a file named "holds_print_list.docx" in the
user's Desktop directory, unless the -o option (/o on Windows) is given with
an explicit file path to use instead.

It accepts various other command-line arguments.  To get information about
the available options, use the -h argument (or /h on Windows).

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2018 by the California Institute of Technology.  This code is
open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

from .__version__ import __version__, __title__, __description__, __url__
from .__version__ import __author__, __email__
from .__version__ import __license__, __copyright__

from .exceptions import UserCancelled, ServiceFailure
