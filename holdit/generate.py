'''
generate.py: code to generate the hold list.
'''

import datetime
from   docx import Document
from   docxcompose.composer import Composer
from   docxtpl import DocxTemplate
import html
import os
import sys
import tempfile

import holdit
from holdit.files import holdit_path, module_path, readable
from holdit.exceptions import InternalError


# Global constants.
# .............................................................................

_DEFAULT_TEMPLATE = 'default_template.docx'


# Printing code.
# .............................................................................

def generate_printable_doc(records_list, explicit_template):
    num_pages = len(records_list)
    if num_pages < 1:
        return None
    template = explicit_template or normal_template()
    if not readable(template):
        raise InternalError('Cannot find a template file for printing.')
    date_time_stamps = current_date_and_time()

    page_files = []
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
        page_files.append(tmpfile)

    if len(page_files) < 2:
        return doc
    else:
        composer = Composer(Document(page_files[0]))
        for page in page_files[1:]:
            composer.append(Document(page))
        return composer


# Misc. helper code.
# .............................................................................

def normal_template():
    '''Find the path to a template .docx file.  It first looks in the
    directory where Holdit is installed for a filed named "template.docx".
    If no such file is found, it resorts to using a default template file.
    '''
    template = os.path.join(holdit_path(), 'template.docx')
    if not readable(template):
        template = os.path.join(module_path(), _DEFAULT_TEMPLATE)
    return template


def sanitized_string(s):
    # ampersand is bad in XML
    return html.escape(str(s))


def current_date_and_time():
    now = datetime.datetime.now()
    return {'current_date': now.strftime('%d-%m-%Y'),
            'current_time': now.strftime('%I:%M %p').strip('0')}


# Please leave the following for Emacs users.
# .............................................................................
# Local Variables:
# mode: python
# python-indent-offset: 4
# End:
