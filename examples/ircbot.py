from twisted.words.protocols.irc import IRCClient
from twisted.internet import reactor, protocol, ssl
import destiny

class Bot(IRCClient):

    def __init__(self, config, state):
        self.network = config.get('network')
        self.server = config.get('server')
        self.nickname = config.get('nickname')
        self.username = config.get('username')
        self.channels = config.get('channels')
        self.gamertags = config.get('gamertags')
        self.master = config.get('master')
        self.commands = {'crota': cmd_crota}

    def signedOn(self):
        print("Signed on.")
        for channel in self.channels:
            self.join('#' + channel)

    def privmsg(self, user, channel, msg):
        hostmask = user
        nick = user.split('!', 1)[0]
        if (nick == self.master):
            parts = msg.split()
            cmd = parts[0]
            data = parts[1:]
            cmd = self.commands.get(cmd)
            if cmd:
                cmd(data)

    def cmd_crota(self, data):
        if data:
            gt = data
        else:
            for gt in self.gamertags:
                api = destiny.DestinyAPI(1, gt)
                characters = api.CHARACTERS[2]
                for character in characters:
                    pprint(mychar.activity_hash_status(1836893116))
        print("")


class BotFactory(protocol.ReconnectingClientFactory):
    """The queen bot factory, automaticaly attempts to reconnect."""
    def __init__(self, config, state):
        self.config = config
        self.state = state

    def buildProtocol(self, addr):
        p = QueenBot(self.config, self.state)
        p.factory = self
        return p


def main():
    config = {
        'network': 'irc.gorf.us',
        'username': 'debstiny',
        'nickname': 'debstiny',
        'realname': 'debstiny',
        'gamertags': ['ermff',],
        'channels': ['testerm'],
    }
    bot = BotFactory(config)
    if config['ssl']:
        reactor.connectSSL(config['server'], config['ssl'], bot,
                           ssl.ClientContextFactory(),
                           bindAddress=vhost)
    else:
        reactor.connectTCP(config['server'], 6667, bot,
                           bindAddress=vhost)
    reactor.run()


if __name__ == '__main__':
    main()