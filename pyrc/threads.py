import threading

class JobThread(threading.Thread):
  """Thread that executes a job every N milliseconds"""

  def __init__(self, func, reference):
    threading.Thread.__init__(self)
    self._finished = threading.Event()
    self._func = func
    self._reference = reference

  def shutdown(self):
    """Stop this thread"""
    self._finished.set()

  def run(self):
    """Keep running this thread until it's stopped"""
    while not self._finished.isSet():
      self._func(self._reference)
      self._finished.wait(self._func._interval / 1000.0)
