import requests
from config import config


class DestinyAPI(object):

    def __init__(self):
        self.API_URL = 'https://www.bungie.net/Platform/Destiny'
        self.REQUEST_HEADERS = config['REQUEST_HEADERS']

    def _request(self, query):
        req = requests.get(self.API_URL+query, headers=self.REQUEST_HEADERS)
        return req.json()

    def get_membership_id_by_display_name(self, membership_type, display_name):
        query = '/%d/Stats/GetMembershipIdByDisplayName/%s' % (membership_type,
                                                               display_name)
        data = self._request(query)
        return data['Response']

    def get_account_info(self, membership_type, membership_id):
        query = '/%d/Account/%s/' % (membership_type, membership_id)
        data = self._request(query)
        return data

if __name__ == '__main__':
    api = DestinyAPI()
    membership_type = 1  # XBOX: 1, PS: 2
    membership_id = api.get_membership_id_by_display_name(membership_type,
                                                          'ermff')
    print("MEMBERSHIP ID: %s" % membership_id)
    account_info = api.get_account_info(membership_type, membership_id)
    print("ACCOUNT INFO: %s" % account_info)
