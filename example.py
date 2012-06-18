import pyrc
import utils.hooks as hooks

class HerpBot(pyrc.Bot):
  @hooks.command
  def derper(self):
    "will print yo"
    print "yo"

if __name__ == '__main__':
  bot = HerpBot('irc.freenode.net')
  # bot.connect()
  bot.parseline(":derp PRIVMSG #hackerschool :HarpBot, derper")
