import threading

class Thread (threading.Thread):

   call_back = 0

   def __init__(self, call_back):
      threading.Thread.__init__(self)
      self.call_back = call_back

   def run(self):
      self.call_back()