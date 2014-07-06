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
    self.config.setdefault('verbose', True)
    self.config.setdefault('prefix', '%')

    self._inbuffer = ""
    self._commands = []
    self._privmsgs = []
    self._threads = []
    self.socket = None
    self.initialized = False
    self.listeners = {}

    # init funcs
    self._add_listeners()
    self._addhooks()

  def connect(self):
    '''
    Connects to the IRC server with the options defined in `config`
    '''
    self._connect()

    try:
      self._listen()
    except (KeyboardInterrupt, SystemExit):
      pass
    finally:
      self.close()

  def close(self):
    for thread in self._threads:
      thread.shutdown()
    self.socket.shutdown(socket.SHUT_RDWR)
    self.socket.close()

  def _listen(self):
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
        if self.config['verbose']: print line
        self._run_listeners(line)

  def _run_listeners(self, line):
    """
    Each listener's associated regular expression is matched against raw IRC
    input. If there is a match, the listener's associated function is called
    with all the regular expression's matched subgroups.
    """
    for regex, callbacks in self.listeners.iteritems():
      match = regex.match(line)

      if not match:
        continue

      for callback in callbacks:
        callback(*match.groups())

  def _addhooks(self):
    for func in self.__class__.__dict__.values():
      if callable(func) and hasattr(func, '_type'):
        if func._type == 'COMMAND':
          self._commands.append(func)
        elif func._type == 'PRIVMSG':
          self._privmsgs.append(func)
        elif func._type == 'REPEAT':
          thread = threads.JobThread(func, self)
          self._threads.append(thread)
        else:
          raise "This is not a type I've ever heard of."

  def _receivemessage(self, target, sender, message):
    message = message.strip()
    to_continue = True

    if target.startswith("#"):
      suffix = self._strip_prefix(message)
      if suffix:
        to_continue = self._parsefuncs(target, sender, suffix, self._commands)
    else: # if it's not a channel, there's no need to use a prefix or highlight the bot's nick
      to_continue = self._parsefuncs(target, sender, message, self._commands)

    # if no command was executed
    if to_continue:
      to_continue = self._parsefuncs(target, sender, message, self._privmsgs)
  
  def _parsefuncs(self, target, sender, message, funcs):
    for func in funcs:
      match = func._matcher.search(message)
      if match:
        group_dict = match.groupdict()
        groups = match.groups()

        if group_dict and (len(groups) > len(group_dict)):
          # match.groups() also returns named parameters
          raise "You cannot use both named and unnamed parameters"
        elif group_dict:
          func(self, target, sender, **group_dict)
        else:
          func(self, target, sender, *groups)

        if self.config['break_on_match']: return False
    return True

  def _strip_prefix(self, message):
    """
    Checks if the bot was called by a user.
    Returns the suffix if so.

    Prefixes include the bot's nick as well as a set symbol.
    """

    if not hasattr(self, "name_regex"):
      """
      regex example:
      ^(((BotA|BotB)[,:]?\s+)|%)(.+)$
      
      names = [BotA, BotB]
      prefix = %
      """

      names = self.config['names']
      prefix = self.config['prefix']

      name_regex_str = r'^(?:(?:(%s)[,:]?\s+)|%s)(.+)$' % (re.escape("|".join(names)), prefix)
      self.name_regex = re.compile(name_regex_str, re.IGNORECASE)

    search = self.name_regex.search(message)
    if search:
      return search.groups()[1]

    return None

  def _connect(self):
    "Connects a socket to the server using options defined in `config`."
    self.socket = socket.socket()
    self.socket.connect((self.config['host'], self.config['port']))
    self.cmd("NICK %s" % self.config['nick'])
    self.cmd("USER %s %s bla :%s" %
        (self.config['ident'], self.config['host'], self.config['realname']))

  def cmd(self, raw_line):
    if self.config['verbose']: print "> %s" % raw_line
    self.socket.send(raw_line + "\r\n")

  # Higher level interfaces

  def join(self, *channels):
    "High level interface to joining channels."
    self.cmd('JOIN %s' % (' '.join(channels)))

  def part(self, *channels):
    "High level interface to joining channels."
    self.cmd('PART %s' % (' '.join(channels)))

  def message(self, recipient, s):
    "High level interface to sending an IRC message."
    self.cmd("PRIVMSG %s :%s" % (recipient, s))


  def _add_listeners(self):
    self._add_listener(r'^:\S+ 433 .*', self._change_nick)
    self._add_listener(r'^PING :(.*)', self._ping)
    self._add_listener(r'^:(\S+)!\S+ PRIVMSG (\S+) :(.*)', self._privmsg)
    self._add_listener(r'^:(\S+)!\S+ INVITE \S+ :?(.*)', self._invite)
    self._add_listener(r'^\S+ MODE %s :\+([a-zA-Z]+)' % self.config['nick'],
        self._mode)

  def _add_listener(self, regex, func):
    array = self.listeners.setdefault(re.compile(regex), [])
    array.append(func)

  # Default listeners

  def _change_nick(self):
    self.config["nick"] += "_"
    self.cmd("NICK %s" % self.config["nick"])

  def _ping(self, host):
    self.cmd("PONG :%s" % host)

  def _privmsg(self, sender, target, message):
    self._receivemessage(target, sender, message)

  def _invite(self, inviter, channel):
    self.join(channel)

  def _mode(self, modes):
    if 'i' in modes and self._should_autoident():
      self.cmd("PRIVMSG NickServ :identify %s" % self.config['password'])

    # Initialize (join rooms and start threads) if the bot is not
    # auto-identifying, or has just identified.
    if ('r' in modes or not self._should_autoident()) and not self.initialized:
      self.initialized = True
      if self.config['channels']:
        self.join(*self.config['channels'])
      # TODO: This doesn't ensure that threads run at the right time, e.g.
      # after the bot has joined every channel it needs to.
      for thread in self._threads:
        thread.start()

  def _should_autoident(self):
    return self.config['password']
