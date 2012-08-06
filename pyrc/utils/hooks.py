import functools
import re

class command(object):
  def __init__(self, matcher=None):
    self._matcher = matcher

  def __call__(self, func):
    # Default the command's name to the function's name.
    matcher = self._matcher
    if matcher is None:
      matcher = func.func_name

    # convert matcher to regular expression
    matcher = re.compile(matcher)

    @functools.wraps(func)
    def wrapped_command(*args, **kwargs):
      return func(*args, **kwargs)
    wrapped_command._type = "COMMAND"
    wrapped_command._matcher = matcher
    return wrapped_command

def interval(milliseconds):
  def wrapped(func):
    @functools.wraps(func)
    def wrapped_command(*args, **kwargs):
      return func(*args, **kwargs)
    wrapped_command._type = "REPEAT"
    wrapped_command._interval = milliseconds
    return wrapped_command
  return wrapped
