import requests
from config import config
from pprint import pprint


class DestinyAPI(object):

    def __init__(self, membership, username):
        self.API_URL = 'https://www.bungie.net/Platform/Destiny'
        self.REQUEST_HEADERS = config['REQUEST_HEADERS']
        self.MEMBERSHIP = membership
        self.USERNAME = username
        self._membership_id()
        self._account_info()
        self._characters()

    def _api_request(self, qry):

        """Build the API request using query parameter"""

        req = requests.get(self.API_URL+qry,
                           headers=self.REQUEST_HEADERS)
        return req.json()

    def _membership_id(self):

        """Retrieve and set the membership id for a user"""

        qry = '/%d/Stats/GetMembershipIdByDisplayName/%s' % (self.MEMBERSHIP,
                                                             self.USERNAME)
        data = self._api_request(qry)
        self.MEMBERSHIP_ID = data['Response']  # will return 0 if invalid

    def _account_info(self):

        """Retrieve and set the account info for a user"""

        qry = '/%d/Account/%s/' % (self.MEMBERSHIP, self.MEMBERSHIP_ID)
        self.ACCOUNT_INFO = self._api_request(qry)

    def _characters(self):

        """Retrieve and set all the characters for a user"""

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
        self._activities_info()
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

    def _activities_info(self):

        """Retrieve and set all activity info for a character"""

        qry = '/%d/Account/%s/Character/%s/Activities/'
        qry = qry % (self.API.MEMBERSHIP, self.API.MEMBERSHIP_ID,
                     self.CHARACTER_INFO['characterBase']['characterId'])
        self.ACTIVITIES_INFO = self.API._api_request(qry)

    def _activity_hash_info(self, activity_hash):

        """Retrieve general information regarding an activity"""

        qry = '/Manifest/Activity/%d/' % activity_hash
        activity_info = self.API._api_request(qry)
        return activity_info

    def _activity_hash_status(self, activity_hash):

        """Retrieve specific progress information regarding an activity"""

        _activities = self.ACTIVITIES_INFO['Response']['data']['available']
        for activity in _activities:
            if activity_hash == activity['activityHash']:
                return activity

    def _raid_acitivty_hash_status(self, activity_hash):

        """Retrieve specific information regarding weekly raid completion"""

        qry = '/Stats/ActivityHistory/%d/%s/%s'
        qry = qry % (self.API.MEMBERSHIP, self.API.MEMBERSHIP_ID,
                     self.character_id)
        qry = qry + '?page=0&count=1&definitions=true&mode=4'
        print(qry)
        _activities_history = self.API._api_request(qry)
        pprint(_activities_history)

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
    membership = 1  # XBOX: 1, PS: 2
    # username = 'ermff'
    api = DestinyAPI(1, 'ermff')
    character = api.CHARACTERS[1]
    character._raid_acitivty_hash_status(1)



#     weeklys = {'crotanorm': 1836893116, 'weeklyheroichard': 692589233, 'nightfall': 692589232,
# 'voghard': 2659248068, 'vognorm': 2659248071}
