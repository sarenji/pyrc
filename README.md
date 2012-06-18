# pyrc

Slim, concise IRC client. Also cute.

## Installation

TODO.

## Usage

```python
import pyrc
import pyrc.utils.hooks as hooks

class YourBot(pyrc.Bot):
  @hooks.command
  def sayhi(self, channel):
    self.message(channel, "hi!")

if __name__ == '__main__':
  bot = YourBot('irc.freenode.net')
  bot.connect()
```

Then on IRC, after the bot logs in:

```
<davidpeter> HarpBot, sayhi
```

## TODO

* Turn into PyPi package
* Less strict commands. Add ability to define regex commands.
* Fix hacky joining of channels.
