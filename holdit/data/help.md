<h1 align="center">Help for Holdit!</h1>

Basic operation
---------------

<img align="right" width="50%" src=".graphics/holdit-initial-window.png">

_Holdit!_ has both a GUI interface and a command-line interface.  The GUI interface is simple: a user starts the program in a typical way (e.g., by double-clicking the program icon) and _Holdit!_ creates a main window, then immediately begins its work by connecting to Caltech.tind.io and asking the user for login credentials.  The image at right depicts the first dialog. After the user types in a login name and password, and clicks the **OK** button, the program does the following behind the scenes:

1. Searches Caltech.tind.io for the most recent hold requests
2. Scrapes the HTML page returned by the TIND search
3. Downloads the Google spreadsheet used by the Circulation staff
4. Compares the two data sources to determine if the TIND search returned new holds
5. Adds any new hold requests to the Google spreadsheet
6. Creates a Word document listing the latest hold requests (if any)
7. Opens the Word document so that the user can print it

Unless an error occurs, _Holdit!_ presents only one other dialog: to ask the user whether the Google spreadsheet should be opened in a browser window.  If the user clicks the **Yes** button, it's opened.  Either way, _Holdit!_ exits after the user answers the dialog.


Customizing the Word template
-----------------------------

The Word document is created from a template Word file named `template.docx`, which _Holdit!_ looks for in the same folder where the _Holdit!_ program itself is found.  (E.g., on Windows this might be `C:\Program Files\Holdit` or wherever the user installed the application.)

<p align="center"><img width="400px" src=".graphics/holdit-template.png"></p>

Users can modify the look and content of the template as they wish in order to customize the format of the printed hold sheets.  Variables used in the template are indicated by surrounding special terms with `{{` and `}}`; these then get substituted by _Holdit!_ when it generates the printable document.  The following table lists the recognized variables:

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
| `{{current_date}}` | Today's date; i.e., the date when Holdit! generates the hold list |
| `{{current_time}}` | Now; i.e., the the time when when Holdit! generates the hold list |

