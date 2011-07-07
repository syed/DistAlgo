class P(DistProcess):

    def __init__(self, pid, pipe, perf_pipe):
        DistProcess.__init__(self, pid, pipe, perf_pipe)
        self._event_patterns = [EventPattern(Event.receive, 'Request', [], [], [self._event_handler_0]), EventPattern(Event.receive, 'Reply', [], [(1, 'lc')], [self._event_handler_1])]
        self._sent_patterns = []
        self._label_events = {'cs': self._event_patterns, 'start': self._event_patterns, 'end': self._event_patterns, 'reply': self._event_patterns}

    def setup(self, ps):
        self.reqc = None
        self.s = ps
        self.waiting = set()
        self.replied = set()

    def cs(self):
        self._label_('start')
        self.reqc = self.logical_clock()
        self.send(('Request', self.reqc), self.s)
        self._label_('reply')
        while (not (len(self.replied) == len(self.s))):
            self._process_event_(self._event_patterns, True)
        self._label_('cs')
        self.output('In critical section')
        self.work()
        self._label_('end')
        self.reqc = None
        self.output('Is releasing.')
        self.send(('Reply', self.reqc, self._id), self.waiting)
        self.waiting = set()
        self.replied = set()

    def main(self):
        while True:
            self.cs()
            self.work()

    def _event_handler_0(self, _timestamp, _source):
        if ((self.reqc == None) or ((_timestamp, _source) < (self.reqc, self._id))):
            self.send(('Reply', 
            self.logical_clock()), _source)
        else:
            self.waiting.add(_source)

    def _event_handler_1(self, lc, _timestamp, _source):
        if ((self.reqc != None) and (lc > self.reqc)):
            self.replied.add(_source)