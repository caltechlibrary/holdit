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


# Class definitions.
# .............................................................................

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
