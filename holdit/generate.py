'''
generate.py: code to generate the hold list.
'''

from   docxtpl import DocxTemplate
import os
import sys

import holdit
from holdit.files import holdit_path, module_path, readable
from holdit.exceptions import InternalError


# Global constants.
# .............................................................................

_DEFAULT_TEMPLATE = 'default_template.docx'


# Printing code.
# .............................................................................

def generate_printable_doc(records_list, explicit_template = None):
    template = explicit_template if explicit_template else normal_template()
    if not readable(template):
        raise InternalError('Cannot find print template file.')
    doc = DocxTemplate(template)
    doc.render(vars(records_list[0]))
    return doc


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


# Please leave the following for Emacs users.
# .............................................................................
# Local Variables:
# mode: python
# python-indent-offset: 4
# End:
