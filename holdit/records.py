'''
records.py: base record class for holding data
'''


# Class definitions.
# .............................................................................

class HoldRecord(object):
    requester_name = ''               # String
    requester_type = ''               # String
    requester_url = ''                # String

    item_title = ''                   # String
    item_details_url = ''             # String
    item_record_url = ''              # String
    item_call_number = ''
    item_barcode = ''
    item_location_name = ''           # String
    item_location_code = ''           # String
    item_loan_status = ''             # String
    item_loan_url = ''                # String

    date_requested = ''               # String (date)
    date_due = ''                     # String (date)
    date_last_notice_sent = ''        # String (date)
    overdue_notices_count = ''        # String

    holds_count = ''                  # String


# Utility functions.
# .............................................................................

def records_diff(known_records, new_records):
    known_barcodes = [r.item_barcode for r in known_records]
    diffs = []
    for record in new_records:
        if record.item_barcode not in known_barcodes:
            diffs.append(record)
    return diffs


def records_filter(method = 'all'):
    '''Returns a closure that takes a TindRecord and returns True or False,
    depending on whether the record should be included in the output.  This
    is meant to be passed to Python filter() as the test function.
    '''
    # FIXME
    return (lambda x: True)


# Debugging aids.

def print_records(records_list, specific = None):
    for record in records_list:
        print('title: {}\nbarcode: {}\nlocation: {}\ndate requested: {}\nrequester name: {}\nstatus in TIND: {}\n\n'
              .format(record.item_title,
                      record.item_barcode,
                      record.item_location_code,
                      record.date_requested,
                      record.requester_name,
                      record.item_loan_status))


def find_record(barcode, records_list):
    for record in records_list:
        if record.item_barcode == barcode:
            return record
    return None
