'''
generate.py: code to generate the hold list.
'''

import requests
from docopt import docopt
from getpass import getpass
import json
from lxml import html


# Global constants.
# .............................................................................

_USER_AGENT_STRING = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/59.0.3071.109 Chrome/59.0.3071.109 Safari/537.36'


# Login code.
# .............................................................................

def tind_html(user, pswd):
    headers = {
        'connection' : 'keep-alive',
        'user-agent' : _USER_AGENT_STRING,
        'referer'    : 'https%3A//caltech.tind.io/admin2/bibcirculation/requests%3F',
        'origin'     : 'https://caltech.tind.io/youraccount/login',
    }
    login = {
        'timezoneOffset'   : 0,
        'j_username'       : user,
        'j_password'       : pswd,
        '_eventId_proceed' : 'Log In'
    }
    with requests.Session() as session:
        url = 'https://caltech.tind.io/youraccount/shibboleth?referer=/admin2/bibcirculation/requests%3F'
        res = session.get(url, headers = headers, allow_redirects = True)
        tree = html.fromstring(res.content)
        sessionid = session.cookies.get('JSESSIONID')

        next_url = 'https://idp.caltech.edu/idp/profile/SAML2/Redirect/SSO;jsessionid={}?execution=e1s1'.format(sessionid)
        res = session.post(next_url, headers = headers, data = login, allow_redirects = True)
        tree = html.fromstring(res.content)
        SAMLResponse = tree.xpath('//input[@name="SAMLResponse"]')[0].value
        RelayState = tree.xpath('//input[@name="RelayState"]')[0].value

        next_url = tree.xpath('//form[@action]')[0].action
        saml_data = {'SAMLResponse': SAMLResponse, 'RelayState': RelayState}
        res = session.post(next_url, headers = headers, data = saml_data, allow_redirects = True)
        if res.status_code == 200:
            return res.content
        else:
            import pdb; pdb.set_trace()


# Scraping code.
# .............................................................................

def generate_hold_list(user, pswd):
    html = tind_html(user, pswd)




# Please leave the following for Emacs users.
# .............................................................................
# Local Variables:
# mode: python
# python-indent-offset: 4
# End:
