'''
records.py: base record class for holding data

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2018 by the California Institute of Technology.  This code is
open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

import holdit
from holdit.debug import log



# Class definitions.
# .............................................................................
# The particular set of fields in this object came from the TIND holds page
# contents and a few additional fields kept in the tracking spreadsheet by
# the Caltech Library circulation staff.

class HoldRecord(object):
    '''Base class for records describing a hold request.'''

    def __init__(self):
        self.requester_name = ''               # String
        self.requester_type = ''               # String
        self.requester_url = ''                # String

        self.item_title = ''                   # String
        self.item_details_url = ''             # String
        self.item_record_url = ''              # String
        self.item_call_number = ''
        self.item_barcode = ''
        self.item_location_name = ''           # String
        self.item_location_code = ''           # String
        self.item_loan_status = ''             # String
        self.item_loan_url = ''                # String

        self.date_requested = ''               # String (date)
        self.date_due = ''                     # String (date)
        self.date_last_notice_sent = ''        # String (date)
        self.overdue_notices_count = ''        # String

        self.holds_count = ''                  # String


# Utility functions.
# .............................................................................

def records_diff(known_records, new_records):
    '''Returns the records from 'new_records' missing from 'known_records'.
    The comparison is done on the basis of bar codes and request dates.'''
    if __debug__: log('Diffing known records with new records')
    diffs = []
    for candidate in new_records:
        found = [record for record in known_records if same_request(record, candidate)]
        if not found:
            diffs.append(candidate)
    if __debug__: log('Found {} different records', len(diffs))
    return diffs


def same_request(record1, record2):
    return (record1.item_barcode == record2.item_barcode
            and record1.date_requested == record2.date_requested
            and record1.requester_name == record2.requester_name)


def records_filter(method = 'all'):
    '''Returns a closure that takes a TindRecord and returns True or False,
    depending on whether the record should be included in the output.  This
    is meant to be passed to Python filter() as the test function.
    '''
    # FIXME. It seemed like it might be useful to provide filtering features
    # in the future, but this is currently a no-op.
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
