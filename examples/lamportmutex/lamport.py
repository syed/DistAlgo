class P(DistProcess):

    def __init__(self, pid, pipe, perf_pipe):
        DistProcess.__init__(self, pid, pipe, perf_pipe)
        self._event_patterns = [EventPattern(Event.receive, 'Reply', [], [(1, 'c3'), (2, 'p3')], [self._receive_handler_0]), EventPattern(Event.receive, 'Request', [], [], [self._event_handler_1]), EventPattern(Event.receive, 'Release', [], [(1, 'time')], [self._event_handler_2])]
        self._sent_patterns = []
        self._label_events = {'cs': self._event_patterns, 'start': self._event_patterns, 'end': self._event_patterns, 'release': self._event_patterns, 'reply': self._event_patterns}
        self._receive_messages_0 = set()

    def setup(self, ps):
        self.c = 0
        self.q = []
        self.s = ps

    def cs(self):
        self._label_('start')
        reqc = self.logical_clock()
        self.q.append((reqc, self._id))
        self.send(('Request',), self.s)
        self._label_('reply')
        while (not (all((((p2 == self._id) or ((reqc, self._id) <= (c2, p2))) for (c2, p2) in self.q)) and all((any(((c3 > reqc) for c3 in self._has_receive_0(p3))) for p3 in self.s)))):
            self._process_event_(self._event_patterns, True)
        self._label_('cs')
        self.output('In critical section')
        self.work()
        self._label_('release')
        self.q.remove((reqc, self._id))
        self.output('Releasing critical section')
        self.send(('Release', reqc), self.s)
        self._label_('end')
        reqc = None

    def main(self):
        while True:
            self.cs()
            self.work()

    def _event_handler_1(self, _timestamp, _source):
        self.q.append((_timestamp, _source))
        self.send(('Reply', 
        self.logical_clock(), self._id), _source)

    def _event_handler_2(self, time, _timestamp, _source):
        if ((time, _source) in self.q):
            self.q.remove((time, _source))

    def _receive_handler_0(self, _c3, _p3, _timestamp, _source):
        self._receive_messages_0.add((_c3, _p3))

    def _has_receive_0(self, p3):
        return [c3_ for (c3_, p3_) in self._receive_messages_0 if (p3_ == p3)]