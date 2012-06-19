import pyrc
import pyrc.utils.hooks as hooks

class GangstaBot(pyrc.Bot):
  @hooks.command
  def bling(self, channel):
    "will print yo"
    self.message(channel, "yo")

if __name__ == '__main__':
  bot = GangstaBot('irc.freenode.net', channels = ['#turntechgodhead'])
  bot.connect()
