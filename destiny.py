import requests
from config import config
from pprint import pprint

hash_dict = {
    'classes': {
        3655393761: 'Titan',
        2271682572: 'Warlock',
        671679327: 'Hunter'},
    'strikes': {
        3468792474: 'Weekly Heroic Strike Level 30',
        3468792475: 'Weekly Nightfall Strike'
        },
    'raids': {
        1836893116: 'Crota\'s End Level 30',
        2659248068: 'Vault of Glass Level 30',
        2659248071: 'Vault of Glass Level 26'
        },
}


class DestinyAPI(object):

    def __init__(self, membership_type, username):
        self.API_URL = 'https://www.bungie.net/Platform/Destiny'
        self.REQUEST_HEADERS = config['REQUEST_HEADERS']
        self.membership_type = membership_type
        self.username = username

    def _api_request(self, qry):

        """Build the API request using query parameter"""

        req = requests.get(self.API_URL+qry,
                           headers=self.REQUEST_HEADERS)
        return req.json()

    @property
    def membership_id(self):
        qry = '/%d/Stats/GetMembershipIdByDisplayName/%s'
        qry = qry % (self.membership_type, self.username)
        data = self._api_request(qry)
        return data['Response']  # will return 0 if invalid

    @property
    def account_info(self):
        qry = '/%d/Account/%s/' % (self.membership_type, self.membership_id)
        data = self._api_request(qry)
        return data

    @property
    def characters(self):
        data = self.account_info['Response']['data']['characters']
        k = 0
        characters = {}
        for i in data:
            characters[k] = DestinyCharacter(self, i)
            k += 1
        return characters


class DestinyCharacter(object):

    def __init__(self, api, character_info):
        self.api = api
        self.character_info = character_info

    def __repr__(self):
        if self.base_character_level < 20:
            level = self.base_character_level
        else:
            level = self.light_level
        return "<Level %d %s>" % (level, self.character_class)

    def _activity_status(self, activity_hash):

        """Retrieve the status of an activity. Use this for weekly strikes."""

        qry = '/%d/Account/%s/Character/%s/Activities/'
        qry = qry % (self.api.membership_type, self.api.membership_id,
                     self.character_id)
        data = self.api._api_request(qry)
        for activity in self.activities_info['Response']['data']['available']:
            if activity_hash == activity['activityHash']:
                return activity['isCompleted']

    def _raid_activity_status(self, activity_hash):

        """Retrieve status of raid activity. Use this for Crota and VoG"""

        qry = '/Stats/ActivityHistory/%d/%s/%s'
        qry = qry % (self.api.membership_type, self.api.membership_id,
                     self.character_id)
        qry = qry+'?page=0&count=1&definitions=true&mode=4'
        _activities_history = self.api._api_request(qry)
        data = _activities_history['Response']['data']['activities']
        for activity in data:
            reference_id = activity['activityDetails']['referenceId']
            if reference_id == activity_hash:
                completed = activity['values']['completed']['statId']
                return completed
        #return None

    @property
    def activities_info(self):
        qry = '/%d/Account/%s/Character/%s/Activities/'
        qry = qry % (self.api.membership_type, self.api.membership_id,
                     self.character_id)
        data = self.api._api_request(qry+'?definitions=True')
        return data

    @property
    def character_id(self):
        return self.character_info['characterBase']['characterId']

    @property
    def base_character_level(self):
        return self.character_info['baseCharacterLevel']

    @property
    def character_class(self):
        class_hash = self.character_info['characterBase']['classHash']
        return hash_dict['classes'][class_hash]

    @property
    def date_last_played(self):
        return self.character_info['characterBase']['dateLastPlayed']

    @property
    def grimoire_score(self):
        return self.character_info['characterBase']['grimoireScore']

    @property
    def light_level(self):
        return self.character_info['characterBase']['powerLevel']


if __name__ == '__main__':
    api_user = DestinyAPI(1, 'ermff')
    character = api_user.characters[1]
    print(character)
    print(character._activity_status(3468792475))

