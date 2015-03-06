import requests
from config import config
from pprint import pprint


class DestinyAPI(object):

    def __init__(self, platform, username):
        self.API_URL = 'https://www.bungie.net/Platform/Destiny'
        self.REQUEST_HEADERS = config['REQUEST_HEADERS']
        self.PLATFORM = platform
        self.USERNAME = username
        self._membership_id()
        self._account_info()
        self._characters()

    def api_request(self, qry):
        req = requests.get(self.API_URL+qry+'/?definitions=True',
                           headers=self.REQUEST_HEADERS)
        return req.json()

    def _membership_id(self):
        qry = '/%d/Stats/GetMembershipIdByDisplayName/%s' % (self.PLATFORM,
                                                             self.USERNAME)
        data = self.api_request(qry)
        self.MEMBERSHIP = data['Response']  # will return 0 if invalid

    def _account_info(self):
        qry = '/%d/Account/%s/' % (self.PLATFORM, self.MEMBERSHIP)
        self.ACCOUNT_INFO = self.api_request(qry)

    def _characters(self):
        _characters = self.ACCOUNT_INFO['Response']['data']['characters']
        k = 1
        self.CHARACTERS = {}
        for i in _characters:
            self.CHARACTERS[k] = DestinyCharacter(self, i)
            k += 1


class DestinyCharacter(object):

    def __init__(self, api, character_info):
        self.API = api
        self.CHARACTER_INFO = character_info
        self.activities_info()
        self.class_hashes = {3655393761: 'Titan',
                             2271682572: 'Warlock',
                             671679327: 'Hunter'}

    def __repr__(self):
        # pprint(self.CHARACTER_INFO)
        if self.base_character_level < 20:
            level = self.base_character_level
        else:
            level = self.light_level
        return "<Level %d %s>" % (level, self.character_class)

    def activities_info(self):
        """Retrieve all activity info for a character"""
        qry = '/%d/Account/%s/Character/%s/Activities/'
        qry = qry % (self.API.PLATFORM, self.API.MEMBERSHIP,
                     self.CHARACTER_INFO['characterBase']['characterId'])
        self.ACTIVITIES_INFO = self.API.api_request(qry)

    def activity_hash_info(self, activity_hash):
        """Retrieve general information regarding an activity"""
        qry = '/Manifest/Activity/%d/' % activity_hash
        activity_info = self.API.api_request(qry)
        return activity_info

    def activity_hash_status(self, activity_hash):
        """Retrieve specific progress information regarding an activity"""
        _activities = self.ACTIVITIES_INFO['Response']['data']['available']
        for activity in _activities:
            if activity_hash == activity['activityHash']:
                return activity

    @property
    def character_id(self):
        return self.CHARACTER_INFO['characterBase']['characterId']

    @property
    def base_character_level(self):
        return self.CHARACTER_INFO['baseCharacterLevel']

    @property
    def character_class(self):
        class_hash = self.CHARACTER_INFO['characterBase']['classHash']
        return self.class_hashes[class_hash]

    @property
    def date_last_played(self):
        return self.CHARACTER_INFO['characterBase']['dateLastPlayed']

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
    # test
    mychar = api.CHARACTERS[2]
    print(mychar)
    pprint(mychar.activity_hash_status(2659248071))
