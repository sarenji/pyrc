import pyrc
import pyrc.utils.hooks as hooks

class GangstaBot(pyrc.Bot):
  @hooks.command
  def bling(self, channel):
    "will print yo"
    self.message(channel, "yo")

  @hooks.repeat(10000)
  def keeprepeating(self):
    "will say something"
    self.message("#turntechgodhead", "stop repeating myself")

if __name__ == '__main__':
  bot = GangstaBot('irc.freenode.net', channels = ['#turntechgodhead'])
  bot.connect()
