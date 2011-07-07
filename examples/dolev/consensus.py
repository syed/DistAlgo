class P(DistProcess):

    def __init__(self, pid, pipe, perf_pipe):
        DistProcess.__init__(self, pid, pipe, perf_pipe)
        self._event_patterns = [EventPattern(Event.receive, 'Value', [], [(1, 'v')], [self._event_handler_0])]
        self._sent_patterns = []
        self._label_events = {'start': self._event_patterns, 'end': self._event_patterns, 'one_round': self._event_patterns}

    def setup(self, v, mf, ps):
        self.x = (-1)
        self.V = {v: False}
        self.s = ps
        self.maxfail = mf + (1)
        self.receiveflag = False

    def main(self):
        self._label_('start')
        for round in range(1, self.maxfail):
            self._label_('one_round')
            for k in self.V.keys():
                if (not self.V[k]):
                    self.send(('Value', k), self.s)
                    self.V[k] = True
            while (not self.receiveflag):
                self._process_event_(self._event_patterns, True)
            self.receiveflag = False
        self._label_('end')
        for v in self.V.keys():
            self.x = max(self.x, v)
        self.output('x = %d' % (self.x))

    def _event_handler_0(self, v, _timestamp, _source):
        self.receiveflag = True
        if (v not in self.V.keys()):
            self.V[v] = False