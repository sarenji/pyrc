import pyrc
import pyrc.utils.hooks as hooks

class GangstaBot(pyrc.Bot):
  @hooks.command()
  def bling(self, channel, sender):
    "will print yo"
    self.message(channel, "%s: yo" % sender)

  @hooks.command("^repeat\s+(?P<msg>.+)$")
  def repeat(self, channel, sender, **kwargs):
    "will repeat whatever yo say"
    self.message(channel, "%s: %s" % (sender, kwargs["msg"]))

  @hooks.privmsg("(lol|lmao|rofl(mao)?)")
  def stopword(self, channel, sender, *args):
    """
    will repeat 'lol', 'lmao, 'rofl' or 'roflmao' when seen in a message
    """
    self.message(channel, args[0])

  @hooks.interval(10000)
  def keeprepeating(self):
    "will say something"
    self.message("#turntechgodhead", "stop repeating myself")

if __name__ == '__main__':
  bot = GangstaBot('irc.freenode.net', channels = ['#turntechgodhead'])
  bot.connect()
