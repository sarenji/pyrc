import inspect
import sys
import socket
import string
import re

import threads

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
    self.config.setdefault('names', [self.config['nick']])
    self.config.setdefault('ident', nick.lower())
    self.config.setdefault('realname', "A Pyrc Bot")
    self.config.setdefault('channels', [])
    self.config.setdefault('password', None)

    self._inbuffer = ""
    self._commands = []
    self._threads = []
    self.socket = None
    self.initialized = False

    self.addhooks()

  def message(self, recipient, s):
    "High level interface to sending an IRC message."
    self.cmd("PRIVMSG %s :%s" % (recipient, s))

  def connect(self):
    '''
    Connects to the IRC server with the options defined in `config`
    '''
    self._connect()

    try:
      self.listen()
    except (KeyboardInterrupt, SystemExit):
      pass
    finally:
      self.close()

  def listen(self):
    """
    Constantly listens to the input from the server. Since the messages come
    in pieces, we wait until we receive 1 or more full lines to start parsing.

    A new line is defined as ending in \r\n in the RFC, but some servers
    separate by \n. This script takes care of both.
    """
    while True:
      self._inbuffer = self._inbuffer + self.socket.recv(1024)
      # Some IRC servers disregard the RFC and split lines by \n rather than \r\n.

      temp = self._inbuffer.split("\n")
      self._inbuffer = temp.pop()

      for line in temp:
        # Strip \r from \r\n for RFC-compliant IRC servers.
        line = line.rstrip('\r')
        self.parseline(line)
        print line

  def parseline(self, line):
    if line.startswith("PING"):
      length = len("PING ")
      host = line[length:]
      self.cmd("PONG %s" % host)
    elif re.match(r"^:\S+ PRIVMSG", line):
      msg_regex = re.compile(r"^:(\S+)!\S+ PRIVMSG (\S+) :(.*)")
      nick, channel, message = re.match(msg_regex, line).groups()
      self.receivemessage(channel, nick, message)
    elif re.match(r"^:\S+ INVITE %s" % self.config['nick'], line):
      msg_regex = re.compile(r"^:(\S+)!\S+ INVITE \S+ :?(.*)")
      inviter, channel = re.match(msg_regex, line).groups()
      self.cmd("JOIN %s" % channel)
    elif re.match(r"^\S+ MODE %s :\+\w*i" % self.config['nick'], line)\
        and self.config['password']:
      # Autoidentify if a password is provided
      self.cmd("PRIVMSG NickServ :identify %s" % self.config['password'])
    elif re.match(r"^:\S+ MODE", line) and not self.initialized:
      self.initialized = True
      if self.config['channels']:
        self.cmd("JOIN %s" % ' '.join(self.config['channels']))
      # TODO: This doesn't ensure that threads run at the right time, e.g.
      # after the bot has joined every channel it needs to.
      for thread in self._threads:
        thread.start()

  def addhooks(self):
    for func in self.__class__.__dict__.values():
      if callable(func) and hasattr(func, '_type'):
        if func._type == 'COMMAND':
          self._commands.append(func)
        elif func._type == "REPEAT":
          thread = threads.JobThread(func, self)
          self._threads.append(thread)
        else:
          raise "This is not a type I've ever heard of."

  def receivemessage(self, channel, nick, message):
    self.parsecommand(channel, message)

  def parsecommand(self, channel, message):
    # sort names so names that are substrings work
    names = sorted(self.config['names'], key=len, reverse=True)

    name_used = None
    for name in names:
      name_regex_str = r'^(%s)[,:]?\s+' % re.escape(name)
      name_regex = re.compile(name_regex_str, re.IGNORECASE)
      if name_regex.match(message):
        name_used = name_regex.match(message).group(1)
        break

    if not name_used:
      return

    _,_,message = message.partition(name_used)
    command = re.match(r'^[,:]?\s+(.*)', message).group(1)
    for command_func in self._commands:
      match = command_func._matcher.search(command)
      if match:
        command_func(self, channel, *match.groups(), **match.groupdict())

  def cmd(self, raw_line):
    print "> %s" % raw_line
    self.socket.send(raw_line + "\r\n")

  def _connect(self):
    "Connects a socket to the server using options defined in `config`."
    self.socket = socket.socket()
    self.socket.connect((self.config['host'], self.config['port']))
    self.cmd("NICK %s" % self.config['nick'])
    self.cmd("USER %s %s bla :%s" %
        (self.config['ident'], self.config['host'], self.config['realname']))

  def close(self):
    for thread in self._threads:
      thread.shutdown()
    self.socket.shutdown(socket.SHUT_RDWR)
    self.socket.close()
