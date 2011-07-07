class P(DistProcess):

    def __init__(self, pid, pipe, perf_pipe):
        DistProcess.__init__(self, pid, pipe, perf_pipe)
        self._event_patterns = [EventPattern(Event.receive, 'Token', [], [(1, 'g')], [self._event_handler_0]), EventPattern(Event.receive, 'Request', [], [], [self._event_handler_1])]
        self._sent_patterns = []
        self._label_events = {'release': self._event_patterns, 'start': self._event_patterns, 'await': self._event_patterns}

    def setup(self, peers, token):
        self.ps = peers
        self.requested = dict(((p, 0) for p in self.ps))
        self.granted = dict(((p, 0) for p in self.ps))
        self.token_held = token
        self.in_cs = False

    def cs(self):
        self._label_('start')
        if (not self.token_held):
            self.send(('Request',), self.ps)
        self._label_('await')
        while (not self.token_held):
            self._process_event_(self._event_patterns, True)
        self.in_cs = True
        self.output('In CS!')
        self.work()
        self._label_('release')
        self.output('Releasing CS!')
        self.in_cs = False
        self.release()

    def release(self):
        if (self.in_cs or (not self.token_held)):
            return 
        for p in self.ps:
            if (self.requested[p] > self.granted[p]):
                self.token_held = False
                self.send(('Token', self.granted), p)
                break

    def main(self):
        while True:
            self.cs()

    def _event_handler_0(self, g, _timestamp, _source):
        self.granted = g
        self.granted[self._id] = self.logical_clock()
        self.token_held = True

    def _event_handler_1(self, _timestamp, _source):
        self.requested[_source] = max(self.requested[_source], _timestamp)
        self.release()