import requests
import getpass
import os

import bungo_db

class DestinyException(Exception):
  pass

class Destiny(object):

  def __init__(self, api_key=None):
    if not api_key:
      fn = os.path.split(os.path.realpath(__file__))[0]
      fn = os.path.join(fn, 'api_key.txt')
      if os.path.isfile(fn):
        with open(fn, 'r') as f:
          for line in f:
            if line[0] != '#' :
              line = line.strip()
              #test(line)
              api_key = line
            if api_key :
              break
      if not api_key :
        print('Unable to obtain API key from "%s".' % fn)
        print('Please enter your API key.')
        api_key = getpass.getpass("API Key: ")
    self._API_KEY = api_key
    self.API_URL = 'https://www.bungie.net/Platform/Destiny'
    self.db = bungo_db.bungo_db(api_key=api_key)
    self._cache = CachedData()
    self._session = requests.Session()
    self._session.headers['X-API-Key'] = api_key

  def _api_request(self, query, cache=False):
    request_string = self.API_URL + query
    if cache:
      if self._cache.has_key(request_string):
        return self._cache[request_string]
      req = self._session.get(request_string)
      out = req.json()
      self._cache[request_string] = out
      return out
    else:
      req = self._session.get(request_string)
    return req.json()

  def login(self, email, gamer_tag, platform, pw=None):
    pass

  def DestinyAccount(self, membership_type, username):
    return  DestinyAccount(self, membership_type, username)

##############

  def _get_hash(self, string, num, name=False):
    if string[-4:] == 'Hash' :
      string = string[:-4]
    out = self._api_request('/Manifest/%s/%s' % (string, num), cache=True)['Response']['data']
    if name :
      if string in out :
        out = out[string]
      out = out[string + 'Name']
    return out

  def weekly_nightfall_strike():
    pass

  def weekly_heroic_strike():
    pass

  def daily_heroic_story():
    pass

class CachedData(object):
  def __init__(self):
    self._dict = {}
    for attr in ['__len__', '__contains__', '__iter__', 'keys', 'values']:
      setattr(self, attr, getattr(self._dict, attr))

  def __getitem__(self, key):
    try:
      return self._dict[key]
    except KeyError:
      self._dict[key] = CashedData()
    return self._dict[key]

  def __setitem__(self, key, val):
    if type(val) in []:#dict]:#, CachedData]:
      new_val = CachedData()
      for i in val:
        new_val[i] = val[i]
      self._dict[key] = new_val
    else:
      self._dict[key] = val
    return None

  def clear_cache(self):
    for i in self._dict:
      if type(self._dict[i]) == CachedData:
        self._dict[i].clear_cache()
      else :
        self._dict.pop(i)
    return None

  def has_key(self, key):
    return key in self._dict

class DestinyAccount(object):

  def __init__(self, api, membership_type, username):
    self.api = api
    self.membership_type = membership_type
    self.username = username
    self.account_info # this will raise the exception if the user is invalid

  def __repr__(self):
    if self.membership_type == 1 :
      sys = 'Xbox'
    elif self.membership_type == 2 :
      sys = 'PS'
    else :
      sys = '?'
    return '<Destiny Account %s (%s)>' % (self.username, sys)

  @property
  def membership_id(self):
    qry = '/%s/Stats/GetMembershipIdByDisplayName/%s'
    qry = qry % (self.membership_type, self.username)
    data = self.api._api_request(qry, cache=True)
    return data['Response']

  @property
  def account_info(self):
    qry = '/%s/Account/%s/Summary' % (self.membership_type, self.membership_id)
    data = self.api._api_request(qry)
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

  def __init__(self, account, character_info):
    self.account = account
    self.api = account.api
    self.character_info = character_info

  def __repr__(self):
    tmp = (self.base_character_level, self.light_level, self.character_class)
    return "<Level %s, %s %s>" % tmp

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
    qry = qry % (self.account.membership_type, self.account.membership_id,
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
  #   for activity in self.activities_info['Response']['data']['available']:
  #     pprint(activity)
  #     if activity_hash == activity['activityHash']:
  #       return activity['isCompleted']

  # @property
  # def weekly_heroic_status(self):
  #   for activity in self.activities_info['Response']['data']['available']:
  #     qry = '/Manifest/Activity/%s?mode=Strike' % activity['activityHash']
  #     response = self.api._api_request(qry)
  #     activity_name = response['Response']['data']['activity']['activityName']
  #     if activity_name == 'Weekly Heroic Strike':
  #       if activity['isCompleted']:
  #         return 'Completed'
  #       else:
  #         return 'Incomplete'

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
    return self.api.db.Class[class_hash].name

  @property
  def date_last_played(self):
    return self.character_info['characterBase']['dateLastPlayed']

  @property
  def grimoire_score(self):
    return self.character_info['characterBase']['grimoireScore']

  @property
  def light_level(self):
    return self.character_info['characterBase']['powerLevel']

  @property
  def inventory(self):
    qry = '/%s/Account/%s/Character/%s/Inventory/Summary/'
    qry = qry % (self.account.membership_type, self.account.membership_id,
           self.character_id)
    data = self.api._api_request(qry)
    return [itemWrapper(self.api, i, self) for i in
            data['Response']['data']['items']]

def itemWrapper(api, data, character=None):
  itemType = api.db.inventoryBucket[data['bucketHash']].name
  if (itemType.split(' '))[-1] == 'Weapons':
    return DestinyWeapon(api, data, character)
  elif (itemType.split(' '))[-1] == 'Subclass':
    return DestinySubclass(api, data, character)
  else :
    return DestinyItem(api, data, character)

class DestinyItem(object):
  '''This should never be called directly; only through itemWrapper.'''

  def __init__(self, api, data, character=None):
    '''This should never be called directly; only through itemWrapper.'''
    self.api = api
    self.data = data
    self.itemHash = data['itemHash']
    self.owner = character
    self.itemId = data['itemId']

  def __repr__(self):
    tmp = (self.name, self.itemType)
    return "<DestinyItem %s, %s>" % tmp

  @property
  def name(self):
    return self.api.db.inventoryItem[self.itemHash].name

  @property
  def itemType(self):
    out = self.api.db.inventoryBucket[self.data['bucketHash']].name
    if out[-3:] != 'ass' : # there are a lot of class-holes out there
      out = out.rstrip('s')
    return out

  @property
  def instance_details(self):
    if not self.owner :
      return None
    req = '/%s/Account/%s/Character/%s/Inventory/%s/'
    own = self.owner
    acc = self.owner.account
    req = req % (acc.membership_type, acc.membership_id, own.character_id,
                 self.itemId)
    return (self.api._api_request(req, cache=True))['Response']['data']

  @property
  def generic_details(self):
    return self.api.db.inventoryItem[self.itemHash].data

  @property
  def description(self):
    return self.generic_details['itemDescription']

  @property
  def icon_url(self):
    return self.generic_details['icon']

  @property
  def rarity(self):
    return self.generic_details['tierTypeName']

class DestinyEquipment(DestinyItem):
  '''Destiny items that are equipable on a character.'''

  def __init__(self, *args, **kwargs):
    '''This should never be called directly; only through itemWrapper.'''
    super(DestinyEquipment, self).__init__(*args, **kwargs)

  def __repr__(self):
    tmp = (self.name, self.itemType)
    return "<DestinyEqupment %s, %s>" % tmp

  @property
  def perks(self):
    try :
      return self._perks
    except AttributeError:
      self._perks = [ItemPerk(self.api, i) for i in self.details['item']['perks']]
    return self._perks

  @property
  def talentGrid(self):
    return self.api.db.talentGrid[self.generic_details['talentGridHash']].data

class DestinyWeapon(DestinyEquipment):

  def __init__(self, *args, **kwargs):
    '''This should never be called directly; only through itemWrapper.'''
    super(DestinyWeapon, self).__init__(*args, **kwargs)

  def __repr__(self):
    tmp = (self.name, self.itemType)
    return "<DestinyWeapon %s, %s>" % tmp

class DestinySubclass(DestinyEquipment):

  def __init__(self, *args, **kwargs):
    '''This should never be called directly; only through itemWrapper.'''
    super(DestinySubclass, self).__init__(*args, **kwargs)

  def __repr__(self):
    tmp = (self.name, self.parent_class)
    return "<DestinySubclass %s (%s)>" % tmp

  @property
  def parent_class(self):
    tmp = self.api.db.inventoryItem[self.itemHash]['itemTypeName']
    return tmp.split(' ')[0]

class ItemPerk(object):

  def __init__(self, api, data):
    self.api = api
    self.data = data
    self.perkHash = data['perkHash']

  @property
  def name(self):
    return self.api.db.sandboxPerk[self.perkHash].name

  @property
  def details(self):
    return self.api.db.sandboxPerk[self.perkHash].data

  def __repr__(self):
    return "<ItemPerk %s>" % self.name

class talentRow(object):
  def __init__(self, api, data):
    self.api = api
    self.data = data
    self.nodes = [talentNode(api, i) for i in data['steps']]

class talentNode(object):
  def __init__(self, api, data):
    self.api = api
    self.data = data
    self.name = data['nodeStepName']
