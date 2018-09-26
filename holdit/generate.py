'''
generate.py: code to generate the hold list.

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2018 by the California Institute of Technology.  This code is
open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

import datetime
from   docx import Document
from   docxcompose.composer import Composer
from   docxtpl import DocxTemplate
import html
import os
from   os import path
import sys
import tempfile

import holdit
from holdit.files import holdit_path, module_path, readable, datadir_path
from holdit.exceptions import InternalError


# Global constants.
# .............................................................................

_DEFAULT_TEMPLATE = 'default_template.docx'


# Printing code.
# .............................................................................

def printable_doc(records_list, explicit_template):
    '''Generates a Word .docx file with one page for each record. Returns
    a Python docx Document object.'''

    num_pages = len(records_list)
    if num_pages < 1:
        return None
    template = explicit_template or normal_template()
    if not readable(template):
        raise InternalError('Cannot find a template file for printing.')
    date_time_stamps = current_date_and_time()

    # I tried appending directly to the docx and DocxTemplate objects, but
    # the results caused Word to complain that the file was corrupted.  The
    # algorithm below writes out a separate file for each record, then in a
    # subsequent loop, uses docxcompose to combine individual docx Document
    # objects for each file into one overall docx.

    files_list = []
    for index, record in enumerate(records_list):
        tmpfile = tempfile.TemporaryFile()
        doc = DocxTemplate(template)
        values = vars(records_list[index])
        values = {k : sanitized_string(v) for k, v in values.items()}
        values.update(date_time_stamps)
        doc.render(values)
        if index < (num_pages - 1):
            doc.add_page_break()
        doc.save(tmpfile)
        files_list.append(tmpfile)

    if len(files_list) < 2:
        return doc
    else:
        # The only way I found to create a viable single .docx file containing
        # multiple pages is to create separate docx Document objects out of
        # separate actual files (rather than trying to do it all in memory).
        composer = Composer(Document(files_list[0]))
        for page in files_list[1:]:
            composer.append(Document(page))
        return composer


# Misc. helper code.
# .............................................................................

def normal_template():
    '''Finds the path to a template .docx file.  It first looks in the
    directory where Holdit is installed for a filed named "template.docx".
    If no such file is found, it resorts to using a default template file.
    '''
    template = path.join(holdit_path(), 'template.docx')
    if not readable(template):
        template = path.join(datadir_path(), _DEFAULT_TEMPLATE)
    return template


def sanitized_string(s):
    '''Escapes certain problematic characters in the string, like ampersand.'''
    return html.escape(str(s))


def current_date_and_time():
    '''Returns a dictionary of date and time stamp values.'''
    now = datetime.datetime.now()
    return {'current_date': now.strftime('%d-%m-%Y'),
            'current_time': now.strftime('%I:%M %p').strip('0')}


# Please leave the following for Emacs users.
# .............................................................................
# Local Variables:
# mode: python
# python-indent-offset: 4
# End:
