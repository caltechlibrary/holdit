'''
tind.py: code for interacting with Caltech.TIND.io
'''

import json
import requests
from lxml import html
from bs4 import BeautifulSoup

import holdit
from holdit.exceptions import *
from holdit.records import HoldRecord


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


# Class definitions.
# .............................................................................

class TindRecord(HoldRecord):
    '''Class to store structured representations of a TIND hold request.'''

    raw_json = None

    def __init__(self, json_record):
        '''json_record = single 'data' record from the raw json returned by
        the TIND.io ajax call.
        '''
        raw_json = json_record
        self.parse_requester_details(json_record)
        self.parse_item_details(json_record)


    def parse_requester_details(self, json_record):
        relevant_fragment = json_record[0]
        soup = BeautifulSoup(relevant_fragment, features='lxml')
        self.requester_url = soup.a['href']
        self.requester_name = soup.a.get_text().strip()
        self.requester_type = soup.body.small.get_text().strip()


    def parse_item_details(self, json_record):
        relevant_fragment = json_record[1]
        soup = BeautifulSoup(relevant_fragment, features='lxml')
        self.item_details_url = soup.body.a['href']
        self.item_title = soup.body.a.get_text().strip()

        if soup.body.small.find('i'):
            due_string = soup.body.small.i['data-original-title']
            if 'Due date' in due_string:
                start = due_string.find(': ')
                end = due_string.find('\n')
                self.date_due = due_string[start + 2 : end]
            if 'Overdue letters' in due_string:
                start = due_string.find('Overdue letters sent: ')
                self.overdue_notices_count = due_string[start + 22 :]

            self.item_loan_url = soup.body.small.a['href']
            self.item_loan_status = soup.body.small.a.get_text().lower().strip()
        elif 'lost' in str(soup.body.small).lower():
            self.item_loan_status = 'lost'
        elif 'on hold' in str(soup.body.small).lower():
            self.item_loan_status = 'on hold'
        elif 'on shelf' in str(soup.body.small).lower():
            self.item_loan_status = 'on shelf'

        relevant_fragment = json_record[2]
        soup = BeautifulSoup(relevant_fragment, features='lxml')
        self.item_record_url = soup.body.a['href']
        self.item_barcode = soup.body.a.get_text().strip()
        spans = soup.body.find_all('span')
        self.item_call_number = spans[1].get_text().strip()

        relevant_fragment = json_record[3]
        soup = BeautifulSoup(relevant_fragment, features='lxml')
        self.date_requested = soup.body.span.get_text().strip()

        relevant_fragment = json_record[4]
        soup = BeautifulSoup(relevant_fragment, features='lxml')
        self.date_last_notice_sent = soup.span['data-original-title']
        self.overdue_notices_count = soup.span.get_text().strip()

        relevant_fragment = json_record[5]
        soup = BeautifulSoup(relevant_fragment, features='lxml')
        self.holds_count = soup.body.p.get_text().strip()

        relevant_fragment = json_record[6]
        soup = BeautifulSoup(relevant_fragment, features='lxml')
        self.item_location_name = soup.body.span['data-original-title']
        self.item_location_code = soup.body.span.get_text().strip()


# Login code.
# .............................................................................

def records_from_tind(access_handler, notifier):
    json_data = tind_json(access_handler, notifier)
    total_records = json_data['recordsTotal']
    if total_records and total_records[0][0] < 1:
        return []
    num_records = total_records[0][0]
    records = []
    for json_record in json_data['data']:
        tr = TindRecord(json_record)
        # Special hack: the way the holds are being done with Tind, we only
        # need to retrieve the new holds that are marked "on shelf".
        #if 'on shelf' in tr.item_loan_status:
        if 'on shelf' in tr.item_loan_status:
            records.append(tr)
    return records


def tind_json(access_handler, notifier):
    user, pswd = access_handler.name_and_password()
    if not user or not pswd:
        return None
    with requests.Session() as session:
        # Hack the user agent string.
        session.headers.update( { 'user-agent': _USER_AGENT_STRING } )

        # Start with the full destination path + Shibboleth login component.
        res = session.get(_SHIBBED_HOLD_URL, allow_redirects = True)
        if res.status_code >= 300:
            details = 'tind.io shib request returned status {}'.format(res.status_code)
            notifier.msg('Unexpected network result -- please inform developers',
                         details, 'fatal')
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
                         details, 'fatal')
            raise ServiceFailure(details)
        next_url = tree.xpath('//form[@action]')[0].action
        SAMLResponse = tree.xpath('//input[@name="SAMLResponse"]')[0].value
        RelayState = tree.xpath('//input[@name="RelayState"]')[0].value
        saml_payload = {'SAMLResponse': SAMLResponse, 'RelayState': RelayState}
        res = session.post(next_url, data = saml_payload, allow_redirects = True)
        if res.status_code != 200:
            details = 'tind.io action post returned status {}'.format(res.status_code)
            notifier.msg('Caltech.tind.io circulation page failed to respond',
                         details, 'fatal')
            raise ServiceFailure(details)

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
        if res.status_code != 200:
            details = 'tind.io ajax get returned status {}'.format(res.status_code)
            notifier.msg('Caltech.tind.io failed to return hold data',
                         details, 'fatal')
            raise ServiceFailure(details)
        decoded = res.content.decode('utf-8')
        json_data = json.loads(decoded)
        if 'recordsTotal' not in json_data:
            details = 'Could not find a "recordsTotal" field in returned data'
            notifier.msg('Caltech.tind.io return results that we could not intepret',
                         details, 'fatal')
            raise ServiceFailure(details)
        return json_data
