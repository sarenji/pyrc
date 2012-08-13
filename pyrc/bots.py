import inspect
import sys
import socket
import string
import re
import os

import threads

class Bot(object):
  def __init__(self, host, **kwargs):
    '''
    Initializes a new pyrc.Bot.
    '''
    nick = "PyrcBot" if self.__class__ == Bot else self.__class__.__name__
    password = os.environ.get('PASSWORD', None)

    self.config = dict(kwargs)
    self.config.setdefault('host', host)
    self.config.setdefault('port', 6667)
    self.config.setdefault('nick', nick)
    self.config.setdefault('names', [self.config['nick']])
    self.config.setdefault('ident', nick.lower())
    self.config.setdefault('realname', "A Pyrc Bot")
    self.config.setdefault('channels', [])
    self.config.setdefault('password', password)
    self.config.setdefault('break_on_match', True)

    self._inbuffer = ""
    self._commands = []
    self._threads = []
    self.socket = None
    self.initialized = False
    self.listeners = {}

    self.add_listeners()
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
        self.run_listeners(line)
        print line

  def run_listeners(self, line):
    """
    Each listener's associated regular expression is matched against raw IRC
    input. If there is a match, the listener's associated function is called
    with all the regular expression's matched subgroups.
    """
    for regex, callbacks in self.listeners.iteritems():
      match = re.match(regex, line)

      if not match:
        continue

      for callback in callbacks:
        callback(*match.groups())

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
    name = self.name_used(message)

    if not name:
      return

    _,_,message = message.partition(name)
    command = re.match(r'^[,:]?\s+(.*)', message).group(1)
    for command_func in self._commands:
      match = command_func._matcher.search(command)
      if match:
        group_dict = match.groupdict()
        groups = match.groups()
        if group_dict and (len(groups) > len(group_dict)):
          # match.groups() also returns named parameters
          raise "You cannot use both named and unnamed parameters"
        elif group_dict:
          command_func(self, channel, **group_dict)
        else:
          command_func(self, channel, *groups)
        
        if self.config['break_on_match']: break

  def name_used(self, message):
    # sort names so names that are substrings work
    names = sorted(self.config['names'], key=len, reverse=True)

    for name in names:
      name_regex_str = r'^(%s)[,:]?\s+' % re.escape(name)
      name_regex = re.compile(name_regex_str, re.IGNORECASE)
      if name_regex.match(message):
        return name_regex.match(message).group(1)

    return None

  def join(self, *channels):
    self.cmd('JOIN %s' % (' '.join(channels)))

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


  def add_listeners(self):
    self.add_listener(r'^PING :(.*)', self._ping)
    self.add_listener(r'^:(\S+)!\S+ PRIVMSG (\S+) :(.*)', self._privmsg)
    self.add_listener(r'^:(\S+)!\S+ INVITE \S+ :?(.*)', self._invite)
    self.add_listener(r'^\S+ MODE %s :\+([a-zA-Z]+)' % self.config['nick'],
        self._mode)

  def add_listener(self, regex, func):
    array = self.listeners.setdefault(regex, [])
    array.append(func)

  # Default listeners

  def _ping(self, host):
    self.cmd("PONG :%s" % host)

  def _privmsg(self, nick, channel, message):
    self.receivemessage(channel, nick, message)

  def _invite(self, inviter, channel):
    self.join(channel)

  def _mode(self, modes):
    if 'i' in modes and self.should_autoident():
      self.cmd("PRIVMSG NickServ :identify %s" % self.config['password'])

    # Initialize (join rooms and start threads) if the bot is not
    # auto-identifying, or has just identified.
    if ('r' in modes or not self.should_autoident()) and not self.initialized:
      self.initialized = True
      if self.config['channels']:
        self.join(*self.config['channels'])
      # TODO: This doesn't ensure that threads run at the right time, e.g.
      # after the bot has joined every channel it needs to.
      for thread in self._threads:
        thread.start()

  def should_autoident(self):
    return self.config['password']

