import inspect
import sys
import socket
import string
import re

class Bot(object):
  def __init__(self, host, **kwargs):
    '''
    Initializes a new pyrc.Bot.
    '''
    nick = "PyrcBot" if self.__class__ == Bot else self.__class__.__name__
    self.config = dict(kwargs)
    self.config.setdefault('host', host)
    self.config.setdefault('port', 6667)
    self.config.setdefault('nick', nick)
    self.config.setdefault('ident', nick.lower())
    self.config.setdefault('realname', "A Pyrc Bot")
    self.config.setdefault('channels', [])

    self._inbuffer = ""
    self._commands = []
    self.socket = None

    self.parsecommands()

  def message(self, recipient, s):
    "High level interface to sending an IRC message."
    self.cmd("PRIVMSG %s :%s" % (recipient, s))

  def connect(self):
    '''
    Connects to the IRC server with the options defined in `config`
    '''
    self._connect()

    # Constantly listens to the input from the server. Since the messages come
    # in pieces, we wait until we receive 1 or more full lines to start parsing.
    #
    # A new line is defined as ending in \r\n in the RFC, but some servers
    # separate by \n. This script takes care of both.
    while True:
      self._inbuffer = self._inbuffer + self.socket.recv(1024)
      # Some IRC servers disregard the RFC and split lines by \n rather than \r\n.
      temp = string.split(self._inbuffer, "\n")
      self._inbuffer = temp.pop()

      for line in temp:
        # Strip \r from \r\n for RFC-compliant IRC servers.
        line = string.rstrip(line, '\r')
        self.parseline(line)
        print line

  def parseline(self, line):
    if line.startswith("PING"):
      length = len("PING ")
      host = line[length:]
      self.cmd("PONG %s" % host)
    elif re.match(r"^:\S+ PRIVMSG", line):
      self.parsecommand(line)
    elif line.startswith(":" + self.config['nick']):
      # TODO: Improve the above. Should only join on MODE +i or something.
      if len(self.config['channels']) > 0:
        channels = ' '.join(self.config['channels'])
        self.cmd("JOIN " + channels)

  def parsecommands(self):
    for func in self.__class__.__dict__.values():
      if callable(func) and hasattr(func, '_type'):
        if func._type == 'COMMAND':
          self._commands.append(func)
        else:
          raise "This is not a type I've ever heard of."

  def parsecommand(self, line):
    nick_regex = r"^:\S+ PRIVMSG (\S+) :%s[,:]?\s+" % self.config['nick']
    if not re.match(nick_regex, line):
      return

    channel, command = re.match(nick_regex + r'(.*)', line).groups()
    for command_func in self._commands:
      # TODO: Allow for regex matchers
      if command_func._matcher == command:
        command_func(self, channel)

  def cmd(self, raw_line):
    self.socket.send(raw_line + "\r\n")

  def _connect(self):
    "Connects a socket to the server using options defined in `config`."
    self.socket = socket.socket()
    self.socket.connect((self.config['host'], self.config['port']))
    self.cmd("NICK %s" % self.config['nick'])
    self.cmd("USER %s %s bla :%s" %
        (self.config['ident'], self.config['host'], self.config['realname']))
