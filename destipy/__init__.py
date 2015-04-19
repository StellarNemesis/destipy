import requests
import requests_cache
from .hashes import hash_dict


requests_cache.install_cache('destiny_cache')


class DestinyException(Exception):
    pass


class Destiny(object):

    def __init__(self):
        self.API_URL = 'https://www.bungie.net/Platform/Destiny'
        self.REQUEST_HEADERS = {} # = config['REQUEST_HEADERS']
        
    def _api_request(self, query, cache_enabled=True):
        request_string = self.API_URL + query
        if cache_enabled:
            req = requests.get(request_string, headers=self.REQUEST_HEADERS)
        else:
            with requests_cache.disabled():
                req = requests.get(request_string, headers=self.REQUEST_HEADERS)
        return req.json()

    def weekly_nightfall_strike():
        pass

    def weekly_heroic_strike():
        pass

    def daily_heroic_story():
        pass


class DestinyAccount(Destiny):

    def __init__(self, membership_type, username):
        super(DestinyAccount, self).__init__()
        self.membership_type = membership_type
        self.username = username
        self.account_info # this will raise the exception if the user is invalid

    @property
    def membership_id(self):
        qry = '/%s/Stats/GetMembershipIdByDisplayName/%s'
        qry = qry % (self.membership_type, self.username)
        data = self._api_request(qry)
        return data['Response']

    @property
    def account_info(self):
        qry = '/%s/Account/%s/' % (self.membership_type, self.membership_id)
        data = self._api_request(qry)
        try:
            return data['Response']['data']
        except:
            raise DestinyException('Invalid user.')

    @property
    def characters(self):
        data = self.account_info['characters']
        characters = []
        for i in data:
            characters.append(DestinyCharacter(self, i))
        return characters

    @property
    def clan_name(self):
        return self.account_info['clanName'] 

    @property
    def clan_tag(self):
        return self.account_info['clanTag']


class DestinyCharacter(object):

    def __init__(self, api, character_info):
        self.api = api
        self.character_info = character_info

    def __repr__(self):
        if self.base_character_level < 20:
            level = self.base_character_level
        elif self.light_level == 1:
                level = 20
        else:
            level = self.light_level
        return "<Level %s %s>" % (level, self.character_class)

    def _activity_status(self, activity_hash):
        """
            Retrieve the status of an activity. 
            Use this for weekly strikes and daily story.
        """
        for activity in self.activities_info['Response']['data']['available']:
            if activity_hash == activity['activityHash']:
                return activity['isCompleted']

    def _raid_activity_status(self, activity_hash):
        """
            Retrieve status of raid activity. 
            Use this for Crota and VoG.
        """
        qry = '/Stats/ActivityHistory/%s/%s/%s'
        qry = qry % (self.api.membership_type, self.api.membership_id,
                     self.character_id)
        qry = qry+'?page=0&count=5&definitions=true&mode=4'
        response = self.api._api_request(qry)
        data = response['Response']['data']['activities']
        for activity in data:
            reference_id = activity['activityDetails']['referenceId']
            if reference_id == activity_hash:
                completed = activity['values']['completed']['statId']
                if completed:
                    return "Completed"
        return "Incomplete"

    # @property
    # def nightfall_status(self):
    #      for activity in self.activities_info['Response']['data']['available']:
    #         pprint(activity)
    #         if activity_hash == activity['activityHash']:
    #             return activity['isCompleted']

    @property
    def weekly_heroic_status(self):
        for activity in self.activities_info['Response']['data']['available']:
            qry = '/Manifest/Activity/%s?mode=Strike' % activity['activityHash']
            response = self.api._api_request(qry)
            activity_name = response['Response']['data']['activity']['activityName']
            if activity_name == 'Weekly Heroic Strike':
                if activity['isCompleted']:
                    return 'Completed'
                else:
                    return 'Incomplete'

    @property
    def activities_info(self):
        qry = '/%s/Account/%s/Character/%s/Activities/'
        qry = qry % (self.api.membership_type, self.api.membership_id,
                     self.character_id)
        data = self.api._api_request(qry)
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
    