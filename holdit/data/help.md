<h1 align="center">Help for Hold It!</h1>

Basic operation
---------------

<img align="right" width="50%" src=".graphics/holdit-initial-window.png">

_Hold It!_ has both a GUI interface and a command-line interface.  The GUI interface is simple: a user starts the program in a typical way (e.g., by double-clicking the program icon) and _Hold It!_ creates a main window, then immediately begins its work by connecting to Caltech.tind.io and asking the user for login credentials.  The image at right depicts the first dialog. After the user types in a login name and password, and clicks the **OK** button, the program does the following behind the scenes:

1. Searches Caltech.tind.io for the most recent hold requests
2. Scrapes the HTML page returned by the TIND search
3. Downloads the Google spreadsheet used by the Circulation staff
4. Compares the two data sources to determine if the TIND search returned new holds
5. Adds any new hold requests to the Google spreadsheet
6. Creates a Word document listing the latest hold requests (if any)
7. Opens the Word document so that the user can print it

Unless an error occurs, _Hold It!_ presents only one other dialog: to ask the user whether the Google spreadsheet should be opened in a browser window.  If the user clicks the **Yes** button, it's opened.  Either way, _Hold It!_ exits after the user answers the dialog.


How new holds are found
-----------------------

"New holds" are determined in the following way: Hold It searches the circulation list in caltech.tind.io for items with status code 24 (which is the item status "on shelf") and status code 7 (which is the item status "lost"), compares their bar codes and request dates against all entries found in the Google spreadsheet, and writes out the records found in caltech.tind.io but not in the spreadsheet.  The assumption is that when a circulation desk staff processes a hold, they will change that item's status in caltech.tind.io, and thus the search will no longer retrieve it.

<p align="center"><img width="800px" src=".graphics/tind-holds.png"></p>

An implication of this approach is that until the item status is changed in TIND, re-running Hold It will produce the same records.  Hold It also does not rely on any column in the tracking spreadsheet to be changed manually: it only adds rows for records it finds in TIND that have never been entered in the spreadsheet (based on the combination of bar code and request date).  Users are free to fill out the "status" and "staff initials" and other columns in the spreadsheet in whatever way they way.  _Hold It!_ does fill out one column in the spreadsheet, the "HOLDIT USER", to indicate who ran the program when it added rows to the spreadsheet.  This also makes it easier for users to fill out the "STAFF INITIAL" column to manually indicate that a hold has been fulfilled.  (However, changing the spreadsheet does not affect the record in caltech.tind.io.)

<p align="center"><img width="900px" src=".graphics/google-spreadsheet.png"></p>


Customizing the Word template
-----------------------------

The Word document is created from a template Word file named `template.docx`, which _Hold It!_ looks for in the same folder where the _Hold It!_ program itself is found.  (E.g., on Windows this might be `C:\Program Files\Hold It` or wherever the user installed the application.)

<p align="center"><img width="400px" src=".graphics/holdit-template.png"></p>

Users can modify the look and content of the template as they wish in order to customize the format of the printed hold sheets.  Variables used in the template are indicated by surrounding special terms with `{{` and `}}`; these then get substituted by _Hold It!_ when it generates the printable document.  The following table lists the recognized variables:

| Variable | Meaning |
|----------|---------|
| `{{item_title}}` | The title of the book or other item to be held |
| `{{item_details_url}}` | The URL to the "item details" page in Caltech.tind.io |
| `{{item_record_url}}` | The URL to the record editing/update page in Caltech.tind.io | 
| `{{item_call_number}}` | The item's call number |
| `{{item_barcode}}` | A barcode assigned to every item |
| `{{item_location_name}}` | The campus library building where the item is located |
| `{{item_location_code}}` | A code name for the campus library building location |
| `{{item_loan_status}}` | The current status of the item, whether on loan, etc. |
| `{{item_loan_url}}` | The status page for the item's loan status | 
| `{{date_requested}}` | The date the hold request was made | 
| `{{date_due}}` | The date a held item is due back |
| `{{date_last_notice_sent}}` | The date of the most recent reminder notice sent to the patron |
| `{{overdue_notices_count}}` | How many notices have been sent |
| `{{holds_count}}` | How many holds exist on the item |
| `{{requester_name}}` | The name of the patron who requested the hold |
| `{{requester_type}}` | The type of patron (student, faculty, etc.) |
| `{{requester_url}}` | The URL of an information page about the patron |
| `{{caltech_status}}` | The item's status indication in the Google spreadsheet |
| `{{caltech_staff_initials}}` | Who handled the hold request |
| `{{current_date}}` | Today's date; i.e., the date when Hold It! generates the hold list |
| `{{current_time}}` | Now; i.e., the the time when when Hold It! generates the hold list |

