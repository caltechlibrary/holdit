'''
google_sheet.py: code for interacting with the Google spreadsheet for Holds
'''

from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file as oauth_file, client, tools

import holdit
from holdit.exceptions import *
from holdit.records import HoldRecord
from holdit.files import open_url


# Global constants.
# .............................................................................

# If you change this scope, delete the token file and let it be recreated.
_OAUTH_SCOPE = 'https://www.googleapis.com/auth/spreadsheets'

# Where the OAuth token is stored.
_OAUTH_TOKEN_STORE = 'token.json'

# Where to find the configuration file provided by the Google Sheets API.
_CREDENTIALS_STORE = 'credentials.json'

# Set this to a safe spreadsheet when testing, then change this value to the
# actual spreadsheet when moving to production.
_GS_BASE_URL = 'https://docs.google.com/spreadsheets/d/'


# Class definitions.
# .............................................................................

class GoogleHoldRecord(HoldRecord):
    caltech_status = ''
    caltech_staff_initials = ''
    caltech_holdit_user = ''

    def __init__(self, record = None):
        '''Initialize using a TindRecord.'''
        if record:
            self.requester_name        = record.requester_name
            self.requester_type        = record.requester_type
            self.requester_url         = record.requester_url
            self.item_title            = record.item_title
            self.item_details_url      = record.item_details_url
            self.item_record_url       = record.item_record_url
            self.item_call_number      = record.item_call_number
            self.item_barcode          = record.item_barcode
            self.item_location_name    = record.item_location_name
            self.item_location_code    = record.item_location_code
            self.item_loan_status      = record.item_loan_status
            self.item_loan_url         = record.item_loan_url
            self.date_requested        = record.date_requested
            self.date_due              = record.date_due
            self.date_last_notice_sent = record.date_last_notice_sent
            self.overdue_notices_count = record.overdue_notices_count
            self.holds_count           = record.holds_count


# Main code.
# .............................................................................

# The following credentials and connection code is based on the Google examples
# found at https://developers.google.com/sheets/api/quickstart/python

def records_from_google(gs_id, message_handler):
    spreadsheet_rows = spreadsheet_content(gs_id)
    if spreadsheet_rows == []:
        return []
    # First row is the title row.
    results = []
    for index, row in enumerate(spreadsheet_rows[1:], start = 1):
        if not row or len(row) < 8:     # Empty or junk row.
            continue

        record = GoogleHoldRecord()

        cell = row[0]
        end = cell.find('\n')
        if end:
            record.requester_name = cell[:end].strip()
            record.requester_type = cell[end + 1:].strip()
        else:
            record.requester_name = cell.strip()

        cell = row[1]
        end = cell.find('\n')
        if end:
            record.item_title = cell[:end].strip()
            record.item_loan_status = cell[end + 1:].strip()
        else:
            record.item_title = cell.strip()

        cell = row[2]
        end = cell.find('\n')
        if end:
            record.item_barcode = cell[:end]
            record.item_call_number = cell[end + 1:].strip()
        else:
            record.item_title = cell.strip()

        cell = row[3]
        record.date_requested = cell.strip()

        cell = row[4]
        record.overdue_notices_count = cell.strip()

        cell = row[5]
        record.holds_count = cell.strip()

        cell = row[6]
        record.item_location_code = cell.strip()

        if len(row) > 7:
            cell = row[7]
            record.caltech_holdit_user = cell.strip()

        if len(row) > 8:
            cell = row[8]
            record.caltech_status = cell.strip()

        if len(row) > 9:
            cell = row[9]
            record.caltech_staff_initials = cell.strip()

        results.append(record)
    return results


def spreadsheet_credentials():
    store = oauth_file.Storage(_OAUTH_TOKEN_STORE)
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets(_CREDENTIALS_STORE, _OAUTH_SCOPE)
        creds = tools.run_flow(flow, store)
    return creds


def spreadsheet_content(gs_id):
    creds = spreadsheet_credentials()
    service = build('sheets', 'v4', http = creds.authorize(Http()), cache_discovery = False)
    sheets_service = service.spreadsheets().values()
    # If you don't supply a sheet name in the range arg, you get 1st sheet.
    data = sheets_service.get(spreadsheetId = gs_id, range = 'A:Z').execute()
    return data.get('values', [])


def update_google(gs_id, records, message_handler, user):
    data = []
    for record in records:
        record = GoogleHoldRecord(record)
        record.caltech_holdit_user = user
        data.append(google_row_for_record(record))
    if not data:
        return
    creds = spreadsheet_credentials()
    service = build('sheets', 'v4', http = creds.authorize(Http()), cache_discovery = False)
    sheets_service = service.spreadsheets().values()
    body = {'values': data}
    result = sheets_service.append(spreadsheetId = gs_id, range = 'A:Z',
                                   body = body, valueInputOption = 'RAW').execute()


def open_google(gs_id):
    open_url(_GS_BASE_URL + gs_id)


def google_row_for_record(record):
    a = record.requester_name + '\n' + record.requester_type
    b = record.item_title + '\n' + record.item_loan_status
    c = record.item_barcode + '\n' + record.item_call_number
    d = record.date_requested
    e = record.overdue_notices_count
    f = record.holds_count
    g = record.item_location_code
    h = record.caltech_holdit_user
    i = record.caltech_status
    j = record.caltech_staff_initials
    return [a, b, c, d, e, f, g, h, i, j]
