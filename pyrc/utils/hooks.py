def command(func, matcher = None):
  # Default the command's name to the function's name.
  if matcher is None:
    matcher = func.func_name

  def wrapped_command(*args, **kwargs):
    return func(*args, **kwargs)
  wrapped_command._type = "COMMAND"
  wrapped_command._matcher = matcher

  return wrapped_command
