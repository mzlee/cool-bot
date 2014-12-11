#!/usr/bin/env/ python
import os
import sys
import string
import socket

HOST='0.0.0.0'
PORT=6667
NICK='cool-bot'
REALNAME='cool bot'
CHANNEL='#cool-bot'

def connected(fn):
    def deco(self, *args, **kwargs):
        try:
            fn(self, *args, **kwargs)
        except socket.error, err:
            ## Removing the socket
            self._sock = None
        except Exception, err:
            if self._sock:
                self.die(msg = str(err))
    return deco

class CoolBot(object):

    _sock = None
    _lines = [""]

    def _sendmsg(self, cmd, *args):
        self._sock.send("%s %s\n" % (cmd, ' '.join(args)))

    def _buffermsg(self, data):
        lines = data.split('\n')
        self._lines[-1] += lines[0]
        self._lines.extend(lines[1:])

    def _processmsg(self, line):
        print line
        if line.startswith('PING'):
            self.pong()
            return
        line = line[1:]
        if line.find(':') == -1:
            return

        speaker, msg = [l.strip() for l in line.split(':', 1)]
        user, cmd = speaker.split(None, 1)
        if user == "cool-bot!~bot@127.0.0.1":
            ## Ignore messages from myself
            return

        if cmd.startswith('PRIVMSG'):
            channel = cmd.split()[1]
            self._processcmd(user, [channel, ], msg)

    def _processcmd(self, user, channels, raw):
        if not raw.startswith('!!'):
            cmd = raw.split()[0].lower()
            if cmd in ['hi', 'hello', 'sup', 'hey']:
                self.hello(channels, user.split('!')[0])
            return

        cmd, msg = raw.lower(), ""
        try:
            cmd, msg = cmd.split(None, 1)
        except:
            pass

        chunks = msg.split()
        targets = filter(lambda s: s.startswith('@'), chunks)
        for target in targets:
            channels.append(target[1:])
            msg = msg[0:msg.find(target)] + msg[msg.find(target) + len(target) + 1:]
        channels = list(set(channels))
        if 'cool-bot' in channels:
            channels.remove('cool-bot')

        if cmd in self._cmds:
            self._cmds[cmd](channels, msg)
        elif cmd in ['!!part']:
            self.leave(channels, msg)
        elif cmd in ['!!quit', '!!exit', '!!die']:
            self.die(msg = msg)
        elif cmd in ['!!join']:
            self.join([msg])

    def __init__(self, host, port, nick, name, channel):
        self._cmds = {
            '!!all' : self.all,
            '!!say' : self.say,
            '!!help' : self.help,
            '!!die' : self.die,
            '!!leave' : self.leave,
        }
        self.__connect__(host, port)
        self.__identify__(nick, name)
        self.join([channel])

    def __connect__(self, host, port):
        sock = socket.socket()
        sock.connect((host, port))
        self._sock = sock

    @connected
    def __identify__(self, nick, name):
        self._sendmsg('NICK', nick)
        self._sendmsg('USER', 'bot', '0.0.0.0:', name)

    @connected
    def process(self):
        self._buffermsg(self._sock.recv(512))
        while len(self._lines) > 1:
            self._processmsg(self._lines.pop(0))

    @connected
    def all(self, channels, msg = ""):
        self._sendmsg('NAMES', ','.join(channels))

    @connected
    def join(self, channel):
        self._sendmsg('JOIN', channel)

    @connected
    def hello(self, channels, user):
        self.say(channels, 'Hi ' + user)

    @connected
    def say(self, channels, msg, *args):
        msg = ':' + msg
        self._sendmsg('PRIVMSG', ','.join(channels), msg, *args)

    @connected
    def help(self, channels, msg = ""):
        self.say(channels, ', '.join(self._cmds.keys()))

    @connected
    def leave(self, channels, msg):
        for channel in channels:
            self._sendmsg('PART', channel, ':You told me to go.')

    @connected
    def join(self, channels = '#hackerscool'):
        for channel in channels:
            self._sendmsg('JOIN', channel)

    @connected
    def die(self, channel = "", msg = ""):
        if not msg:
            msg = "cool-bot out"
        self._sendmsg('QUIT :%s' % msg)
        self._sock.close()
        self._sock = None

    @connected
    def pong(self):
        self._sendmsg('PONG localhost.')

    def connected(self):
        return self._sock != None

if __name__ == "__main__":
    bot = CoolBot(HOST, PORT, NICK, REALNAME, CHANNEL)
    while bot.connected():
        bot.process()
    
