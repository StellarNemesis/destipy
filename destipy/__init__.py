import requests
import getpass
import os
import shutil
import zipfile
import json

import bungo_db
import bungie_login

try:
  from get_gnome_key import login_info
except ImportError:
  pass

parrent_dir = os.path.split(os.path.realpath(__file__))[0]
_default_platform = 2

class DestinyException(Exception):
  pass

class Destiny(object):

  def __init__(self, api_key=None):
    '''Intialize the Destiny API backend.'''
    self.API_URL = 'https://www.bungie.net/Platform/Destiny'
    self._cache = CachedData()
    self._tested_key = None

    # if api key is not supplied then get one
    if not api_key:
      # see if we have one on file
      fn = os.path.join(parrent_dir, 'api_key.txt')
      if os.path.isfile(fn):
        with open(fn, 'r') as f:
          # each line not beginning with '#' may be a key
          for line in f:
            if line[0] != '#' :
              line = line.strip()
              api_key = line
            # once we have a valid key, stop searching
            if self._test_api_key(api_key) :
              self._tested_key = api_key
              break
      # if we don't have a valid key, then ask user for one
      if not  self._test_api_key(api_key) :
        print('Unable to obtain valid API key from "%s".' % fn)
        print('Please enter your API key.')
        api_key = raw_input("API Key: ")
        if not self._test_api_key(api_key):
          print('Invalid API key entered.')
          print('Visit https://www.bungie.net/en/User/API to obtain API key.')
          while not self._test_api_key(api_key):
            api_key = raw_input("API Key: ")
        # now we have a valid key. See if user wants to save it
        print('Do you want to save your API key to file (%s)?' % fn)
        write_api = None
        while not write_api in ['y', 'n', 'yes', 'no']:
          write_api = raw_input('y/n: ').lower()
        if write_api[0] == 'y':
          if os.path.isfile(fn):
            mode = 'a'
          else:
            mode = 'w'
          with open(fn, mode) as f:
            f.write(api_key)

    self._API_KEY = api_key
    self._tested_key = api_key
    # all api requests are handled trough this session
    self._session = requests.Session()
    self._session.headers['X-API-Key'] = api_key
    # load Bungie's SQL file and download it if necessary
    self.db = self._grab_bungo_db()
    try:
      self.login()
    except:
      pass

  def _test_api_key(self, api_key=None):
    '''Test if api_key is valid (valid => True).'''
    if not api_key:
      try:
        api_key = self._API_KEY
      except AttributeError:
        return False
    if api_key == self._tested_key:
      return True
    req_url = self.API_URL + '/Manifest'
    req = requests.get(req_url, headers={'X-API-Key' : api_key})
    if not req.status_code == 200:
      return False
    out = req.json()['ErrorCode'] == 1
    return out

  def _grab_bungo_db(self, del_old=True):
    '''Load Bungie's SQL manifest if we have an up to date one.
    Download it if we don't.'''
    # see what the newest version is
    resp = self._api_request('/Manifest')['Response']
    version = resp['version']

    # if we have a SQL file saved check the version
    try :
      db = bungo_db.bungo_db()
      renew = db._older_than(version)
    except RuntimeError:
      renew = True

    if renew :
      # time to get new SQL file
      url = 'https://www.bungie.net' + resp['mobileWorldContentPaths']['en']
      zip_fn = os.path.join(parrent_dir, '_tmp_file.zip')
      print('Downloading SQL file %s.' %url)
      r = self._session.get(url, stream=True)
      with open(zip_fn, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
          if chunk: # filter out keep-alive new chunks
            f.write(chunk)
      # unzip SQL file
      zip_ref = zipfile.ZipFile(zip_fn, 'r')
      zip_ref.extractall(parrent_dir)
      zip_ref.close()

      # rename SQL file based on version name
      loc0 = os.path.join(parrent_dir, url.split('/')[-1])
      loc1 = os.path.join(parrent_dir, version + '___bungo-db.sql')
      shutil.move(loc0, loc1)

      # delete now obsolete zip file
      os.remove(zip_fn)
      # delete old SQL file because we won't use it again
      if del_old:
        try :
          os.remove(db._fn)
          del db
        except UnboundLocalError:
          pass

      # load new SQL file
      db = bungo_db.bungo_db(fn=loc1)

    return db

  def _api_request(self, query, params={}, cache=False):
    '''Send a 'get' request to the Destiny API. 'cache' saves response to memory.'''
    request_string = self.API_URL + query
    if cache:
      # check if we've loaded this before
      if self._cache.has_key(request_string):
        return self._cache[request_string]
      req = self._session.get(request_string, params=params)
      out = req.json()
      # save to memory
      self._cache[request_string] = out
      return out
    else:
      req = self._session.get(request_string)
    return req.json()

  def _api_post(self, query, data={}, body=''):
    '''Send a 'post' to the Destiny API.'''
    request_string = self.API_URL + query
    req = self._session.post(request_string, data=json.dumps(data))
    return req.json()

  def login(self, username=None, platform=None, password=None):
    '''Login to PSN or Xbox Live.
    !CURRENTLY XBOX LIVE LOGIN IS NOT IMPLEMENTED!
    Usage: login(username, platform, password=None)
    Usernames for PSN are email addresses.
    Platform values : xbox (1) or psn (2).
    If password is not given it will be prompted.
    '''
    if not platform:
      platform = _default_platform
    if not username and not password:
      try :
        username, password = login_info(platform)
      except NameError:
        pass
    if not username:
      raise ValueError('Cannot obtain username.')
    if not password:
      # get password from user
      try:
        password = getpass.getpass("Enter Password: ")
      except EOFError:
        print('Unable to provide echoless prompt.')
        password = raw_input("Enter Password: ")
    # parse platform entry
    try :
      platform = platform.lower()
    except AttributeError:
      pass
    if platform in [1, 'xbox', 'xbone']:
      # login to xbox live
      try :
        bungie_login.xbox_login(username, password, self._session)
      except AttributeError:
        raise DestinyException('Xbox Live login is currently not implemented.')
    elif platform in [2, 'ps', 'psn', 'ps4', 'ps3', 'playstation', 'best'] :
      # login to psn
      bungie_login.psn_login(username, password, self._session)
    else:
      raise DestinyError('Cannot parse platform "%s".' % platform)

    return None

  def equipItems(self, items, character):
    if not hasattr(items, '__iter__'):
      items = [items]
    params = {'characterId' : character.character_id,
        'membershipType' : character.character_info['characterBase']['membershipType'],
        'itemIds' : [i.itemId for i in items]}
    return self._api_post('/EquipItems', params)

  def transferItems(self, item, character):
    params = {'characterId' : character.character_id,
        'membershipType' : character.character_info['characterBase']['membershipType'],
        'itemId' : item.itemId}
    return self._api_post('/TransferItems', params)

  def DestinyAccount(self, membership_type, username):
    '''Return account info for a Destiny account.'''
    return  DestinyAccount(self, membership_type, username)

##############

  def weekly_nightfall_strike():
    pass

  def weekly_heroic_strike():
    pass

  def daily_heroic_story():
    pass

class CachedData(object):
  def __init__(self):
    '''Creates an empty cache to store data in.'''
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
    for i in self._dict.keys():
      if type(self._dict[i]) == CachedData:
        self._dict[i].clear_cache()
      else :
        self._dict.pop(i)
    return None

  def has_key(self, key):
    return key in self._dict

class DestinyAccount(object):

  def __init__(self, api, membership_type, username):
    '''Load info from a destiny account.'''
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
    # gives membership id number
    qry = '/%s/Stats/GetMembershipIdByDisplayName/%s'
    qry = qry % (self.membership_type, self.username)
    data = self.api._api_request(qry, cache=True)
    return data['Response']

  @property
  def account_info(self):
    # Returns account info or raises error if user is invalid
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

  @property
  def vault(self):
    req = '/%s/MyAccount/Vault/'
    req %= (self.membership_type)
    info = self.api._api_request(req, params={'acountId' : self.membership_id})
    cha = self.characters[0]
    out = {}
    for b in info['Response']['data']['buckets']:
      bucketHash = b['bucketHash']
      key = self.api.db.inventoryBucket[bucketHash].name
      items = []
      for i in b['items']:
        i['bucketHash'] = bucketHash
        items.append(itemWrapper(self.api, i, cha))
      out[key] = items
    return out

class DestinyCharacter(object):
  def __init__(self, account, character_info):
    '''Returns Destiny character.'''
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

  @property
  def equipedItems(self):
    return [i for i in self.inventory if getattr(i, 'isEquipped', False)]

def itemWrapper(api, data, character=None):
  '''Handle item data and construct the proper item child class.
  Optional character input is the owner/holder of the item.
  This function should be the only method used to construct items.'''
  try :
    itemType = api.db.inventoryBucket[data['bucketHash']].name
  except KeyError:
    itemType = api.db.inventoryItem[data['itemHash']].data
    itemType = api.db.inventoryBucket[itemType['bucketTypeHash']].name
  last = (itemType.split(' '))[-1]
  if last == 'Weapons':
    out = DestinyWeapon(api, data, character)
  elif last == 'Subclass':
    out = DestinySubclass(api, data, character)
  elif last in ['Armor', 'Ghost', 'Helmet', 'Gauntlets', 'Artifacts']:
    out = DestinyArmor(api, data, character)
  else :
    out = DestinyItem(api, data, character)
  if out.name == 'Encrypted Engram':
    out = DestinyItem(api, data, character)
  return out

class DestinyItem(object):
  '''This should never be called directly; only through itemWrapper.'''

  def __init__(self, api, data, character=None):
    '''This should never be called directly; only through itemWrapper.'''
    self.api = api
    self.data = data
    self.itemHash = data['itemHash']
    self.owner = character
    try:
      self.itemId = data['itemId']
    except KeyError:
       self.itemId = data['itemInstanceId']
    self.name = api.db.inventoryItem[self.itemHash].name

  def __repr__(self):
    tmp = (self.name, self.itemType)
    return "<DestinyItem %s, %s>" % tmp

  @property
  def itemType(self):
    out = self.api.db.inventoryBucket[self.data['bucketHash']].name
    if out[-3:] != 'ass' : # haha ass...
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
    return (self.api._api_request(req))['Response']['data']

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
    return talentGrid(self.api, self.api.db.talentGrid[self.generic_details['talentGridHash']].data)

  @property
  def activeNodes(self):
    node_info = self.instance_details['item']['nodes']
    nodes = self.talentGrid.nodes
    out = []
    for i in node_info:
      if i['isActivated']:
        node = nodes[i['nodeHash']]
        node._setStep(i['stepIndex'])
        if node.name :
          out.append(node)
    return out

  @property
  def isEquipped(self):
    return self.instance_details['item']['isEquipped']

class DestinyWeapon(DestinyEquipment):

  def __init__(self, *args, **kwargs):
    '''This should never be called directly; only through itemWrapper.'''
    super(DestinyWeapon, self).__init__(*args, **kwargs)

  def __repr__(self):
    tmp = (self.name, self.itemType)
    return "<DestinyWeapon %s, %s>" % tmp

class DestinyArmor(DestinyEquipment):

  def __init__(self, *args, **kwargs):
    '''This should never be called directly; only through itemWrapper.'''
    super(DestinyArmor, self).__init__(*args, **kwargs)

  def __repr__(self):
    tmp = (self.name, self.itemType)
    return "<DestinyArmor %s, %s>" % tmp

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

class itemPerk(object):

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

class talentGrid(object):
  def __init__(self, api, data):
    self.api = api
    self.data = data
    self.nodes = [talentNode(api, i) for i in data['nodes']]

class talentNode(object):
  def __init__(self, api, data, step=None):
    self.api = api
    self.data = data
    for i in ['nodeHash', 'steps', 'nodeHash', 'row', 'column']:
      setattr(self, i, data[i])
    if len(self.steps) == 1:
      self._setStep(0)
    else:
      self.name = 'random perk'
      self.perks = []

  def _setStep(self, step):
    try:
      self.name = self.steps[step]['nodeStepName']
    except KeyError:
      self.name = ''
    self.step = self.steps[step]
    self.perks = [itemPerk(self.api, self.api.db.sandboxPerk[i]) for i in
                  self.step['perkHashes']]

  def __repr__(self):
    return '<TalentNode %s>' % self.name
