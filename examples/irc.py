import sys
sys.path.append("..") # this isn't necessary outside of my testing
import destipy
import asyncore, asynchat
import socket


class IRCClient(asynchat.async_chat):

    def __init__(self, config): 
        asynchat.async_chat.__init__(self)
        self.set_terminator(bytes('\r\n', 'UTF-8'))
        self.collect_incoming_data = self._collect_incoming_data
        self.server = config['server']
        self.port = config['port']
        self.nickname = config['nickname']
        self.username = config['username']
        self.realname = config['realname']
        self.channel = config['channel']
        self.hooked = {
            b'PING':self.on_ping,
            b'KICK':self.on_kick,
            b'PRIVMSG':self.on_privmsg,
            b'433':self.on_nicknameused,
            b'001':self.on_connect,
        }
        self.connect()
    
    def connect(self):
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        asynchat.async_chat.connect(self, (self.server, self.port))
        print("[!] %s connecting to %s on port %s" % (self.nickname, self.server, 
                                                      self.port))

    def handle_connect(self):
        self.sendline('USER %s * * :%s' % (self.username, self.realname))
        self.sendline('NICK %s' % self.nickname)
        print("[!] %s connected!" % self.nickname)

    def sendline(self, line):
        s = bytes('%s\r\n' % line, 'UTF-8')
        self.push(s)
                
    def recvline(self, prefix, command, params):
        i = self.hooked.get(command)
        if i:
            i(prefix, params)
            return 

    def found_terminator(self):
        data = self._get_data()
        prefix = ''
        trailing = []
        if data:
            if data.startswith(b':'): 
                prefix, data = data[1:].split(b' ', 1)
            if data.find(b' :') != -1:
                data, trailing = data.split(b' :', 1)
                params = data.split()
                params.append(trailing)
            else:
                params = data.split()
        command = params.pop(0)
        self.recvline(prefix, command, params)
        
    def on_ping(self, prefix, params):
        self.sendline('PONG %s' % ' '.join(params.decode('UTF-8')))

    def on_connect(self, prefix, params):
        self.connected = True
        self.sendline('JOIN %s' % self.channel)
        print("[!] Joining %s" % self.channel)

    def on_kick(self, prefix, params):
        nickname = prefix.split('!')[0]
        channel = params[0]
        print("[!] %s was kicked from %s" % nickname, channel)

    def on_nicknameused(self, prefix, params):
        self.sendline('NICK %s_' % self.nickname)

    def on_privmsg(self, prefix, params):
        nickname = prefix.split(b'!')[0]
        channel = params[0]
        msg = params[1].split()
        cmd = msg[0]
        if cmd == b'exit':
            sys.exit()
        elif cmd == b'lc':
            error_string = "PRIVMSG %s :lc [platform (xbox=1, ps=2)] [username]" % (self.channel)
            try:
                platform = msg[1]
                username = b' '.join(msg[2:])
            except:
                self.sendline(self.sendline(error_string))
            else:
                if platform not in (b'1',b'2'):
                    self.sendline(error_string)
                else:
                    print(username.decode('utf-8'))
                    try:
                        api_user = destipy.DestinyAPI(platform.decode('utf-8'), username.decode('utf-8'))
                    except:
                       self.sendline(error_string)
                    else:
                        print(api_user.characters[0])
                        for _, character in enumerate(api_user.characters):
                            self.sendline("PRIVMSG %s :%s %s" % (self.channel, _, character)) 

if __name__ == '__main__':
    config = {'server': 'irc.freenode.net', 
              'port': 6667, 
              'channel': '#destipy', 
              'username': 'destipy', 
              'realname': 'destipy', 
              'nickname': 'destipy',}
    bot = IRCClient(config)
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        sys.exit(0)