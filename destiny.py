import requests
from config import config


class DestinyAPI(object):

    def __init__(self):
        self.API_URL = 'https://www.bungie.net/Platform/Destiny'
        self.MEMBERSHIP_TYPE = config['MEMBERSHIP_TYPE']  # XBOX = 1, PS = 2
        self.REQUEST_HEADERS = config['REQUEST_HEADERS']

    def _request(self, query):
        req = requests.get(self.API_URL+query, headers=self.REQUEST_HEADERS)
        return req.json()

    def get_membership_id_by_display_name(self, display_name):
        query = '/%d/Stats/GetMembershipIdByDisplayName/%s' % (self.MEMBERSHIP_TYPE,
                                                               display_name)
        response = self._request(query)
        return response['Response']

    def get_account_info(self, membership_id):
        query = '/%d/Account/%s/' % (self.MEMBERSHIP_TYPE, membership_id)
        response = self._request(query)
        return response

if __name__ == '__main__':
    api = DestinyAPI()
    membership_id = api.get_membership_id_by_display_name('ermff')
    print("MEMBERSHIP ID: %s" % membership_id)
    account_info = api.get_account_info(membership_id)
    print("ACCOUNT INFO: %s" % account_info)
