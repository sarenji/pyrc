import sys
import socket
import string

HOST = "irc.freenode.net"
PORT = 6667
NICK = "HarpBot"
IDENT = "derpbot"
REALNAME = "David's Bot"
inbuffer = ""

s = socket.socket()
s.connect((HOST, PORT))
s.send("NICK %s\r\n" % NICK)
s.send("USER %s %s bla :%s\r\n" % (IDENT, HOST, REALNAME))

while True:
  inbuffer = inbuffer + s.recv(1024)
  # Some IRC servers disregard the RFC and split lines by \n rather than \r\n.
  temp = string.split(inbuffer, "\n")
  inbuffer = temp.pop()

  for line in temp:
    print line

    # Strip \r from \r\n for RFC-compliant IRC servers.
    line = string.rstrip(line, '\r')
    line = string.split(line, None, 1)

    # Lines may be single words.
    command = line[0]
    message = line[1] if len(line) > 1 else ""

    if command == "PING":
      s.send("PONG %s\r\n" % message)

    if command == ":" + NICK:
      s.send("JOIN #turntechgodhead\r\n")
