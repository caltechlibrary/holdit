'''
tind.py: code for interacting with Caltech.TIND.io
'''

import requests
from docopt import docopt
from getpass import getpass
import json
from lxml import html
from bs4 import BeautifulSoup

import holdit
from holdit.exceptions import *


# Global constants.
# .............................................................................

_USER_AGENT_STRING = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/59.0.3071.109 Chrome/59.0.3071.109 Safari/537.36'
'''
Using a user-agent string that identifies a browser seems to be important
in order to make Shibboleth or TIND return results.
'''

_SHIBBED_HOLD_URL = 'https://caltech.tind.io/youraccount/shibboleth?referer=/admin2/bibcirculation/requests%3F%23item_statuses%3D24%26sort%3Drequest_date%26sort_dir%3Dasc'
'''
The hold list URL, via the Caltech Shibboleth login.
'''


# Login code.
# .............................................................................

def tind_json(access_handler, notifier):
    # returns a tuple: (data, success)
    # user, pswd = access_handler.name_and_password()
    user = 'mhucka'
    pswd = '<@cit4me!>'
    if not user or not pswd:
        return None, False
    with requests.Session() as session:
        # Hack the user agent string.
        session.headers.update( { 'user-agent': _USER_AGENT_STRING } )

        # Start with the full destination path + Shibboleth login component.
        res = session.get(_SHIBBED_HOLD_URL, allow_redirects = True)
        if res.status_code >= 300:
            details = 'tind.io shib request returned status {}'.format(res.status_code)
            notifier.msg('Unexpected network result -- please inform developers',
                         details, 'error')
            raise ServiceFailure(details)

        # Now do the login step.
        tree = html.fromstring(res.content)
        sessionid = session.cookies.get('JSESSIONID')
        next_url = 'https://idp.caltech.edu/idp/profile/SAML2/Redirect/SSO;jsessionid={}?execution=e1s1'.format(sessionid)
        login = {
            'timezoneOffset'   : 0,
            'j_username'       : user,
            'j_password'       : pswd,
            '_eventId_proceed' : 'Log In'
        }
        res = session.post(next_url, data = login, allow_redirects = True)
        while str(res.content).find('Forgot your password') > 0:
            if notifier.yes_no('Incorrect login. Try again?'):
                user, pswd = access_handler.name_and_password()
                res = session.post(next_url, data = login, allow_redirects = True)
            else:
                raise UserCancelled

        # Extract the SAML data and follow through with the action url.
        # This is needed to get the necessary cookies into the session object.
        tree = html.fromstring(res.content)
        if not tree.xpath('//form[@action]'):
            details = 'Caltech Shib access result does not have expected form'
            notifier.msg('Unexpected network result -- please inform developers',
                         details, 'error')
            raise ServiceFailure(details)
        next_url = tree.xpath('//form[@action]')[0].action
        SAMLResponse = tree.xpath('//input[@name="SAMLResponse"]')[0].value
        RelayState = tree.xpath('//input[@name="RelayState"]')[0].value
        saml_payload = {'SAMLResponse': SAMLResponse, 'RelayState': RelayState}
        res = session.post(next_url, data = saml_payload, allow_redirects = True)

        # At this point, the session object has Invenio session cookies and
        # Shibboleth IDP session data.  We also have the TIND page we want,
        # but there's a catch: the TIND page contains a table that is filled
        # in using AJAX.  The table in the HTML we have at this point is
        # empty!  We need to fake the AJAX call to retrieve the data that is
        # used by TIND's javascript (in their bibcirculation.js) to fill in
        # the table.  I found this gnarly URL by studying the network
        # requests made by the page when it's loaded.

        ajax_url = 'https://caltech.tind.io/admin2/bibcirculation/requests?draw=1&order%5B0%5D%5Bdir%5D=asc&start=0&length=100&search%5Bvalue%5D=&search%5Bregex%5D=false&sort=request_date&sort_dir=asc'
        ajax_headers = {"X-Requested-With": "XMLHttpRequest",
                        "User-Agent": _USER_AGENT_STRING}
        res = session.get(ajax_url, headers = ajax_headers)
        if res.status_code == 200:
            return res.content, True
        else:
            return None, False
