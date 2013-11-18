import pyrc
import pyrc.utils.hooks as hooks

class GangstaBot(pyrc.Bot):
  @hooks.command()
  def bling(self, channel, sender):
    "will print yo"
    self.message(channel, "%s: yo" % sender)

  @hooks.interval(10000)
  def keeprepeating(self):
    "will say something"
    self.message("#turntechgodhead", "stop repeating myself")

if __name__ == '__main__':
  bot = GangstaBot('irc.freenode.net', channels = ['#turntechgodhead'])
  bot.connect()
