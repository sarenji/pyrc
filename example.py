import pyrc
import pyrc.utils.hooks as hooks

class HerpBot(pyrc.Bot):
  @hooks.command
  def derper(self, channel):
    "will print yo"
    self.message(channel, "yo")

if __name__ == '__main__':
  bot = HerpBot('irc.freenode.net')
  bot.connect()
