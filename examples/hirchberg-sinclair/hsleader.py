class P(DistProcess):

    def __init__(self, pid, pipe, perf_pipe):
        DistProcess.__init__(self, pid, pipe, perf_pipe)
        self._event_patterns = [EventPattern(Event.receive, 'Token', [], [(1, 'v'), (2, 'direction'), (3, 'h')], [self._event_handler_0])]
        self._sent_patterns = []
        self._label_events = {}

    def setup(self, left, right):
        self.left = left
        self.right = right
        self.status = 'Unknown'
        (self.phase_left, self.phase_right) = (False, False)
        self.phase = 0

    def main(self):
        while True:
            self.send(('Token', self._id, 'out', 1 << (self.phase)), self.left)
            self.send(('Token', self._id, 'out', 1 << (self.phase)), self.right)
            while (not ((self.status == 'Leader') or (self.phase_left and self.phase_right))):
                self._process_event_(self._event_patterns, True)
            if (self.status == 'Leader'):
                self.output('I am leader at phase %d!' % (self.phase))
                break
            else:
                self.phase+=1
                (self.phase_left, self.phase_right) = (False, False)

    def _event_handler_0(self, v, direction, h, _timestamp, _source):
        if ((_source == self.left) and (direction == 'out')):
            if ((v > self._id) and (h > 1)):
                self.send(('Token', v, 'out', h - (1)), self.right)
            elif ((v > self._id) and (h == 1)):
                self.send(('Token', v, 'in', 1), self.left)
            elif (v == self._id):
                self.status = 'Leader'
        elif ((_source == self.right) and (direction == 'out')):
            if ((v > self._id) and (h > 1)):
                self.send(('Token', v, 'out', h - (1)), self.left)
            elif ((v > self._id) and (h == 1)):
                self.send(('Token', v, 'in', 1), self.right)
            elif (v == self._id):
                self.status = 'Leader'
        elif ((_source == self.left) and (direction == 'in')):
            if (v > self._id):
                self.send(('Token', v, 'in', 1), self.right)
            elif (v == self._id):
                self.phase_left = True
        elif ((_source == self.right) and (direction == 'in')):
            if (v > self._id):
                self.send(('Token', v, 'in', 1), self.left)
            elif (v == self._id):
                self.phase_right = True