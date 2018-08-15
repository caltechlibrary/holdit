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
    '''Returns the records from 'new_records' missing from 'known_records'.
    The comparison is done on the basis of bar codes and request dates.'''
    diffs = []
    for candidate in new_records:
        matched = [record for record in known_records
                   if record.item_barcode == candidate.item_barcode]
        if not matched:
            diffs.append(candidate)
        else:
            for record in matched:
                if candidate.date_requested != record.date_requested:
                    diffs.append(candidate)
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
