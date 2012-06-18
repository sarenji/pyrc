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
    self.config = dict(kwargs)
    self.config.setdefault('host', host)
    self.config.setdefault('port', 6667)
    self.config.setdefault('nick', "HarpBot")
    self.config.setdefault('ident', "harpbot")
    self.config.setdefault('realname', "David's Bot")

    self._inbuffer = ""
    self._commands = []
    self.socket = None

    self.parsecommands()

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
      self._inbuffer = self._inbuffer + s.recv(1024)
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
      s.send("PONG %s\r\n" % message)
    elif re.match(r"^:[^\s:]+ PRIVMSG", line):
      # We don't need the metadata for the PRIVMSG.
      line = re.sub(r"^\S+ PRIVMSG \S+\s+:", '', line)
      self.parsecommand(line)
    elif line.startswith(":" + self.config['nick']):
      s.send("JOIN #turntechgodhead\r\n")

  def parsecommands(self):
    for func in self.__class__.__dict__.values():
      if callable(func) and hasattr(func, '_type'):
        if func._type == 'COMMAND':
          self._commands.append(func)
        else:
          raise "This is not a type I've ever heard of."

  def parsecommand(self, line):
    nick_regex = r"^%s[,:]?\s" % self.config['nick']
    if not re.match(nick_regex, line):
      return

    command_name = re.sub(nick_regex, '', line)
    for command_func in self._commands:
      # TODO: Allow for regex matchers
      if command_func._matcher == command_name:
        command_func(self)

  def cmd(self, raw_line):
    self.socket.send(raw_line + "\r\n")

  def _connect(self):
    "Connects a socket to the server using options defined in `config`."
    self.socket = socket.socket()
    self.socket.connect((self.config['host'], self.config['port']))
    self.cmd("NICK %s" % self.config['nick'])
    self.cmd("USER %s %s bla :%s" %
        (self.config['ident'], self.config['host'], self.config['realname']))
