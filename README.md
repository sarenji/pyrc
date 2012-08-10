# pyrc

Slim, concise IRC client. Also cute.

## Installation

```bash
$ pip install pyrc
```

## Usage

```python
import pyrc
import pyrc.utils.hooks as hooks

class HiBot(pyrc.Bot):
  @hooks.command()
  def sayhi(self, channel):
    self.message(channel, "hi!")

if __name__ == '__main__':
  bot = HiBot('irc.freenode.net', channels = ['#your_channel'])
  bot.connect()
```

Then on IRC, after the bot logs in:

```
<davidpeter> HiBot, sayhi
<HiBot> hi!
```

## TODO

* Modularize library better.
* Make syntax more like Flask.
