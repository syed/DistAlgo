class P(DistProcess):

    def __init__(self, pid, pipe, perf_pipe):
        DistProcess.__init__(self, pid, pipe, perf_pipe)
        self._event_patterns = [EventPattern(Event.receive, 'Request', [], [], [self._event_handler_0]), EventPattern(Event.receive, 'Token', [], [], [self._event_handler_1])]
        self._sent_patterns = []
        self._label_events = {'release': self._event_patterns, 'await': self._event_patterns, 'request': self._event_patterns}

    def setup(self, otherp):
        self.ps = otherp
        self.token = dict(((p, 0) for p in self.ps + ([self._id])))
        self.requests = dict(((p, 0) for p in self.ps))
        self.token_held = False
        self.token_present = False
        self.token_received = False

    def set_token(self, hastoken):
        self.token_present = hastoken

    def cs(self):
        self._label_('request')
        if (not self.token_present):
            self.send(('Request',), self.ps)
        self._label_('await')
        while (not self.token_received):
            self._process_event_(self._event_patterns, True)
        self.token_present = True
        self.token_held = True
        self.output('In CS!')
        self.work()
        self._label_('release')
        self.output('Release CS!')
        self.token_received = False
        self.release()

    def release(self):
        self.token[self._id] = self.logical_clock()
        self.token_held = False
        for p in self.ps:
            if ((self.requests[p] > self.token[p]) and self.token_present):
                self.token_present = False
                self.output('Sending token to %d' % (p))
                self.send(('Token',), p)

    def run(self):
        while True:
            self.cs()

    def _event_handler_0(self, _timestamp, _source):
        self.requests[_source] = max(self.requests[_source], _timestamp)
        if (self.token_present and (not self.token_held)):
            self.release()

    def _event_handler_1(self, _timestamp, _source):
        self.token_received = True