import requests
from config import config
from pprint import pprint


class DestinyAPI(object):

    def __init__(self, platform, username):
        self.API_URL = 'https://www.bungie.net/Platform/Destiny'
        self.REQUEST_HEADERS = config['REQUEST_HEADERS']
        self.PLATFORM = platform
        self.USERNAME = username
        self.membership_id()

    def _request(self, query):
        req = requests.get(self.API_URL+query, headers=self.REQUEST_HEADERS)
        return req.json()

    def membership_id(self):
        query = '/%d/Stats/GetMembershipIdByDisplayName/%s' % (self.PLATFORM,
                                                               self.USERNAME)
        data = self._request(query)
        self.MEMBERSHIP_ID = data['Response']

    @property
    def account_info(self):
        query = '/%d/Account/%s/' % (self.PLATFORM, self.MEMBERSHIP_ID)
        data = self._request(query)
        return data


class DestinyCharacter(object):

    def __init__(self, api, character_id):
        self.api = api
        self.CHARACTER_ID = character_id

    @property
    def activity_info(self):
        query = '/%d/Account/%s/Character/%s/Activities/' % (self.api.PLATFORM,
                                                             self.api.MEMBERSHIP_ID,
                                                             self.CHARACTER_ID)
        data = self._request(query)
        return data

if __name__ == '__main__':
    platform = 1  # XBOX: 1, PS: 2
    username = 'ermff'
    api = DestinyAPI(platform, username)
    characters = api.account_info['Response']['data']['characters']
    print(characters)
