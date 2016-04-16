import sqlite3 as lite
try:
  import simplejson as json
except ImportError:
  import json
import os
import glob

cp_dict_attr = ['__getitem__', '__len__', '__contains__', '__iter__', 'keys', 'values']
parrent_dir = os.path.split(os.path.realpath(__file__))[0]

def _signed_2_unsigned(integer, size=32):
  '''Convert a signed int to an unsigned int.'''
  out = integer
  if out < 0 : out += 2**size
  return out

def _unsigned_2_signed(integer, size=32):
  '''Convert an unsigned int to a signed int.'''
  out = integer
  if out >= 2**(size-1)  : out -= 2**size
  return out

def _sql_2_dict(sql_db_fn):
  '''Read SQL file into a dictionary.'''
  con = lite.connect(sql_db_fn)
  cur = con.cursor()
  cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
  tables = [f[0] for f in cur.fetchall()]
  out = {}
  for table in tables:
    cur.execute("SELECT * FROM %s" % table)
    out[table] = {_signed_2_unsigned(f[0]): json.loads(f[1])
                  for f in cur.fetchall()}
  return out

def print_names(db, table):
  '''Print the name of all the loaded entries in a table.'''
  name = table[7].lower() + table[8:-10] + 'Name'
  for i in db[table]:
    try :
        out = db[table][i][name], ',', i
    except KeyError:
        out = ('????? ,', i)
    print(' '.join(out))

def a_lt_b(a, b):
  '''Compare version numbers of SQL files.'''
  try :
    if not a:
      return True
    if a == -1 :
      return True
    a = a.split('.')
    b = b.split('.')
    for i in [1, 2, 3, 0]:
      if int(a[i]) < int(b[i]) :
        return True
      if int(a[i]) > int(b[i]) :
        return False
    a = a[-1].split('-')
    b = a[-1].split('-')
    for i in [0, 1]:
      if int(a[i]) < int(b[i]) :
        return True
      if int(a[i]) > int(b[i]) :
        return False
    return False
  except IndexError:
    return True

class sql_version(object):
  def __init__(self, version):
    '''Initiate class for SQL version.'''
    self.version = version

  def __repr__(self):
    return '<SQL Version: %s>' % self.version

  # this allows for sorting of lists of versions.
  def __lt__(self, other_ver):
    try :
      other_ver = other_ver.version
    except AttributeError:
      pass
    a = a_lt_b(self.version, other_ver)
    if not a:
      return a
    return not a_lt_b(other_ver, self.version)

class bungo_db(object):
  def __init__(self, fn=None, fully_loaded=False):
    '''Read/load SQL file. If optional bool 'fully_loaded' then the whole SQL file is loaded into a dictionary. This can take several seconds if you have an older computer.'''
    if not fn:
      # if fn is not provided look for SQL files in the install dir.
      files = glob.glob(os.path.join(parrent_dir, '*___bungo-db.sql'))
      if not files :
        raise RuntimeError('Unable to locate SQL file in "%s".' % parrent_dir)
      # find the file with the newest version
      my_key = lambda fn : sql_version(os.path.split(fn)[-1][:-15])
      files.sort(key=my_key)
      fn = files[-1]
    self._fn = fn
    self._fully_loaded_bool = fully_loaded
    self.data = self._sql_2_tbl(fn)
    # make this class have some dictionary attributes
    for attr in cp_dict_attr:
      if not hasattr(self, attr):
        setattr(self, attr, getattr(self.data, attr))
    # save each table as a class attribute
    for table in self.values():
      if not table.short in ['class']:
        setattr(self, table.short, table)
      elif table.short == 'class' :
        setattr(self, 'Class', table)
    # if we have no tables then this isn't a valid SQL file
    if not self.tables :
      raise RuntimeError('Unable to read SQL file "%s".' % fn)
    # save the files version number
    tmp = '___bungo-db.sql'
    if fn[-len(tmp):] == tmp:
      version = os.path.split(fn)[-1][:-len(tmp)]
    else :
      version = -1
    self.version = sql_version(version)

  def __getitem__(self, key):
    try :
      return self.data[key]
    except KeyError:
      pass
    try :
      key = 'Destiny' + key[0].upper() + key[1:] + 'Definition'
    except TypeError:
      raise KeyError(key)
    return self.data[key]

  @property
  def tables(self):
    return self.values()

  def _fully_loaded(self):
    '''Load the whole SQL file into a dictionary like structure.'''
    self._fully_loaded_bool = True
    for i in self.tables : i._fully_loaded()

  def _sql_2_tbl(self, sql_db_fn):
    '''Read the tables from the SQL file, and put them in a dictionary.'''
    con = lite.connect(sql_db_fn)
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [f[0] for f in cur.fetchall()]
    out = {table: bungo_table(table, cur, fully_loaded=self._fully_loaded_bool)
           for table in tables}
    return out

  def _older_than(self, version):
    return self.version < sql_version(version)

class bungo_table(object):
  def __init__(self, name, cur, fully_loaded=False):
    '''Create/load SQL table. fully_loaded loads all data into a dictionary,
    otherwise data is read from SQL file when it's requested.'''
    self.table_name = name
    self.short = name[7].lower() + name[8:-10]
    self._cur = cur
    self._data = {}
    if fully_loaded :
      self._fully_loaded()
    return None

  def __repr__(self):
    return "<Bungie SQL Table %s>" % self.table_name

  def __getitem__(self, key):
    # if we've already requested this item pull it from memory
    if key in self._data :
      return self._data[key]
    try :
      # read entry from SQL file
      key2 = _unsigned_2_signed(key)
      cmd = "SELECT json FROM %s WHERE id=%s" % (self.table_name, key2)
      self._cur.execute(cmd)
      out = bungo_json(self.short, self._cur.fetchone()[0])
    except TypeError:
      raise KeyError(key)
    # save requested data for later use.
    self._data[key] = out
    return out

  @property
  def loaded_names(self):
    return [(i.name, i.Hash) for i in self._data.values()]

  def _fully_loaded(self):
    '''Load all data into self._data dict.'''
    self._cur.execute("SELECT * FROM %s" % self.table_name)
    self._data = {_signed_2_unsigned(f[0]): bungo_json(self.short, f[1])
                  for f in self._cur.fetchall()}
    for attr in cp_dict_attr:
      setattr(self, attr, getattr(self._data, attr))
    self.names = [(i.name, i.Hash) for i in self._data.values()]
    return None

class bungo_json():
  def __init__(self, short_table, data):
    '''Initialize object for json entry in SQL file.'''
    self.data = json.loads(data)
    self._short = short_table
    for attr in cp_dict_attr:
      setattr(self, attr, getattr(self.data, attr))

  def __repr__(self):
    name = self.name
    if not name : name = self.Hash
    if not name : name = '(Unnamed)'
    return "<Bungie SQL Entry for %s>" % self.name

  def _g0(self, key):
    '''Get item wrapper which returns None on KeyError.'''
    try : return self[key]
    except KeyError : pass

  def grabber(self, string):
    '''Try to semi-intelligently grab data from the object.'''
    out = self._g0(self._short + string)
    if not out :
      headers = ['inventory']
      for head in headers :
        n = len(head)
        if self._short[:n] == head :
          short = self._short[n].lower() + self._short[n+1:]
          out = self._g0(short + string)
    if not out :
      if self._short == 'sandboxPerk' and string == 'Name':
        out = self._g0('displayName')
    return out

  @property
  def name(self):
    return self.grabber('Name')

  @property
  def Hash(self):
    try :
      out = self[self._short + 'Hash']
    except KeyError :
      try :
        out = self['hash']
      except KeyError :
        out = None
    return out

