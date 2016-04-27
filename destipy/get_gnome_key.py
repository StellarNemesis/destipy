#!/usr/bin/env python

import gnomekeyring as gk

_logins = ['xbox', 'https://store.playstation.com/']

def login_info(sys=2, username=None, keyring=None):
  if not keyring:
    keyring = gk.get_default_keyring_sync()
  param = {'signon_realm': _logins[sys - 1]}
  if username :
    param['username_value': username]
  keys = gk.find_items_sync(0, param)
  if len(keys) > 1:
    raise ValueError('More than one key found.')
  if not username:
    username = keys[0].attributes['username_value']
  return username, keys[0].secret
