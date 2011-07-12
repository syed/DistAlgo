class P(DistProcess):

    def __init__(self, pid, pipe, perf_pipe):
        DistProcess.__init__(self, pid, pipe, perf_pipe)
        self._event_patterns = [EventPattern(Event.receive, 'Election', [], [], [self._event_handler_0]), EventPattern(Event.receive, 'Leader', [], [], [self._event_handler_1])]
        self._sent_patterns = []
        self._label_events = {'start': self._event_patterns, 'end': self._event_patterns, 'wait_for_result': self._event_patterns}

    def setup(self, nextid):
        self.next = nextid
        self.awake = True
        self.leaderid = None

    def main(self):
        self._label_('start')
        self.send(('Election',), self.next)
        self.awake = True
        self._label_('wait_for_result')
        while (not (not self.awake)):
            self._process_event_(self._event_patterns, True)
        self._label_('end')
        self.output('Leader is %d.' % (self.leaderid))

    def _event_handler_0(self, _timestamp, _source):
        if (_source > self._id):
            self.send(('Election',), self.next)
        elif ((_source < self._id) and (not self.awake)):
            self.send(('Election',), self.next)
        elif (_source == self._id):
            self.send(('Leader',), self.next)
        self.awake = True

    def _event_handler_1(self, _timestamp, _source):
        self.leaderid = _source
        self.awake = False
        if (_source != self._id):
            self.send(('Leader',), self.next)