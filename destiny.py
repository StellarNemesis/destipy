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
        self.characters()

    def _request(self, qry):
        req = requests.get(self.API_URL+qry, headers=self.REQUEST_HEADERS)
        return req.json()

    def membership_id(self):
        qry = '/%d/Stats/GetMembershipIdByDisplayName/%s' % (self.PLATFORM,
                                                             self.USERNAME)
        data = self._request(qry)
        self.MEMBERSHIP = data['Response']  # will return 0 if invalid

    def characters(self):
        _characters = self.account_info['Response']['data']['characters']
        self.CHARACTERS = [DestinyCharacter(self, i) for i in _characters]

    @property
    def account_info(self):
        qry = '/%d/Account/%s/' % (self.PLATFORM, self.MEMBERSHIP)
        data = self._request(qry)
        return data


class DestinyCharacter(object):

    def __init__(self, api, character_info):
        self.API = api
        self.CHARACTER_INFO = character_info
        self.activity_info()
        self.character_hashes = {'Titan': 3655393761, 'Warlock': 2271682572,
                                 'Hunter': 671679327}

    def activity_info(self):
        qry = '/%d/Account/%s/Character/%s/Activities/'
        qry = qry % (self.API.PLATFORM, self.API.MEMBERSHIP,
                     self.CHARACTER_INFO['characterBase']['characterId'])
        self.ACTIVITY_INFO = self.API._request(qry)

    @property
    def character_id(self):
        return self.CHARACTER_INFO['characterBase']['characterId']

    @property
    def base_character_level(self):
        return self.CHARACTER_INFO['base_character_level']

    @property
    def character_class(self):
        class_hash = self.CHARACTER_INFO['characterBase']['classHash']
        return character_hashes[class_hash]

    @property
    def date_last_played(self):
        return self.CHARACTER_INFO['characterBase']['dateLastPlayed']

    @property
    def grimoire_score(self):
        return self.CHARACTER_INFO['characterBase']['grimoireScore']

    @property
    def grimoire_score(self):
        return self.CHARACTER_INFO['characterBase']['grimoireScore']

    @property
    def light_level(self):
        return self.CHARACTER_INFO['characterBase']['powerLevel']

if __name__ == '__main__':
    platform = 1  # XBOX: 1, PS: 2
    username = 'ermff'
    api = DestinyAPI(platform, username)
    for i in api.CHARACTERS:
        pprint(i.ACTIVITY_INFO)
