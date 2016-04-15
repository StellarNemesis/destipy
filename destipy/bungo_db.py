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
  out = integer
  if out < 0 : out += 2**size
  return out

def _unsigned_2_signed(integer, size=32):
  out = integer
  if out >= 2**(size-1)  : out -= 2**size
  return out

def _sql_2_dict(sql_db_fn):
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
  name = table[7].lower() + table[8:-10] + 'Name'
  for i in db[table]:
    try :
        out = db[table][i][name], ',', i
    except KeyError:
        out = ('????? ,', i)
    print(' '.join(out))

def _a_older_than_b(a, b):
  try :
    if not a:
      return True
    if a == -1 :
      return True
    a = a.split('.')
    b = b.split('.')
    for i in [1, 2, 3, 0]:
      if a[i] < b[i] :
        return True
      if a[i] > b[i] :
        return False
    a = a[-1].split('-')
    b = a[-1].split('-')
    for i in [0, 1]:
      if a[i] < b[i] :
        return True
      if a[i] > b[i] :
        return False
    return False
  except :
    return True

class bungo_db():
  def __init__(self, fn=None, api_key=None, fully_loaded=False):
    if not fn:
      files = glob.glob(os.path.join(parrent_dir, '*___bungo-db.sql'))
      if not files :
        raise RuntimeError('Unable to locate SQL file in "%s".' % parrent_dir)

    self._fn = fn
    self._fully_loaded_bool = fully_loaded
    self.data = self._sql_2_tbl(fn)
    for attr in cp_dict_attr:
      setattr(self, attr, getattr(self.data, attr))
    for table in self.values():
      if not table.short in ['class']:
        setattr(self, table.short, table)
      elif table.short == 'class' :
        setattr(self, 'Class', table)
    if not self.tables :
      raise RuntimeError('Unable to read SQL file "%s".' % fn)
    tmp = '___bungo-db.sql'
    if fn[-len(tmp):] == tmp:
      self.version = fn[:-len(tmp)]
    else:
      self.version = -1

  @property
  def tables(self):
    return self.values()

  def _fully_loaded(self):
    self._fully_loaded_bool = True
    for i in self.tables : i._fully_loaded()

  def _sql_2_tbl(self, sql_db_fn):
    con = lite.connect(sql_db_fn)
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [f[0] for f in cur.fetchall()]
    out = {table: bungo_table(table, cur, fully_loaded=self._fully_loaded_bool)
           for table in tables}
    return out

  def _older_than(self, version):
    return _a_older_than_b(self.version, version)

class bungo_table():
  def __init__(self, name, cur, fully_loaded=False):
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
    if key in self._data :
      return self._data[key]
    try :
      key2 = _unsigned_2_signed(key)
      cmd = "SELECT json FROM %s WHERE id=%s" % (self.table_name, key2)
      self._cur.execute(cmd)
      out = bungo_json(self.short, self._cur.fetchone()[0])
    except TypeError:
      raise KeyError(key)
    self._data[key] = out
    return out

  @property
  def loaded_names(self):
    return [(i.name, i.Hash) for i in self._data.values()]

  def _fully_loaded(self):
    self._cur.execute("SELECT * FROM %s" % self.table_name)
    self._data = {_signed_2_unsigned(f[0]): bungo_json(self.short, f[1])
                  for f in self._cur.fetchall()}
    for attr in cp_dict_attr:
      setattr(self, attr, getattr(self._data, attr))
    self.names = [(i.name, i.Hash) for i in self._data.values()]
    return None

class bungo_json():
  def __init__(self, short_table, data):
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
    try : return self[key]
    except KeyError : pass

  def grabber(self, string):
    out = self._g0(self._short + string)
    if not out :
      headers = ['inventory']
      for head in headers :
        n = len(head)
        if self._short[:n] == head :
          short = self._short[n].lower() + self._short[n+1:]
          out = self._g0(short + string)
    if not out :
      if self._short == 'sandboxPerk':
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

