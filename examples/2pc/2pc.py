from random import randint


class Proposer(DistProcess):

    def __init__(self, pid, pipe, perf_pipe):
        DistProcess.__init__(self, pid, pipe, perf_pipe)
        self._event_patterns = [EventPattern(Event.receive, 'Agree', [], [(1, 'ballot'), (2, 'src')], [self._receive_handler_0]), EventPattern(Event.receive, 'Deny', [], [(1, 'ballot'), (2, 'src')], [self._receive_handler_1])]
        self._sent_patterns = []
        self._label_events = {'transact_end': self._event_patterns, 'transact_start': self._event_patterns}
        self._receive_messages_0 = set()
        self._receive_messages_1 = set()

    def setup(self, nodes, increment):
        self.ballot = self._id
        self.value = self._id
        self.increment = increment
        self.nodes = nodes

    def main(self):
        retry = 0
        while True:
            self._label_('transact_start')
            retry+=1
            self.send(('Prepare', self.ballot, self.value), self.nodes)
            __await_timer_1 = time.time()
            _timeout = False
            while (not (len(self._has_receive_0(self.ballot)) + (len(self._has_receive_1(self.ballot))) == 
            len(self.nodes))):
                self._process_event_(self._event_patterns, True)
                if (time.time() - (__await_timer_1) > TIMEOUT):
                    _timeout = True
                    break
            if (len(self._has_receive_0(self.ballot)) == len(self.nodes)):
                self.send(('Commit', self.ballot), self.nodes)
                self.output('Committed ballot %d on %dth attempt' % ((self.ballot, retry)))
                retry = 0
                self.ballot+=self.increment
                break
            else:
                self.send(('Abort', self.ballot), self.nodes)
                retry+=1
            self._label_('transact_end')

    def _receive_handler_0(self, _ballot, _src, _timestamp, _source):
        self._receive_messages_0.add((_ballot, _src))

    def _has_receive_0(self, ballot):
        return [src_ for (ballot_, src_) in self._receive_messages_0 if (ballot_ == ballot)]

    def _receive_handler_1(self, _ballot, _src, _timestamp, _source):
        self._receive_messages_1.add((_ballot, _src))

    def _has_receive_1(self, ballot):
        return [src_ for (ballot_, src_) in self._receive_messages_1 if (ballot_ == ballot)]


class Acceptor(DistProcess):

    def __init__(self, pid, pipe, perf_pipe):
        DistProcess.__init__(self, pid, pipe, perf_pipe)
        self._event_patterns = [EventPattern(Event.receive, 'Prepare', [], [(1, 'ballot'), (2, 'value')], [self._event_handler_0]), EventPattern(Event.receive, 'Commit', [], [(1, 'ballot')], [self._event_handler_1]), EventPattern(Event.receive, 'Abort', [], [(1, 'ballot')], [self._event_handler_2])]
        self._sent_patterns = []
        self._label_events = {}

    def setup(self, rate):
        self.failure_rate = rate
        self.staging = {}
        self.localdb = {}

    def main(self):
        while (not False):
            self._process_event_(self._event_patterns, True)

    def _event_handler_0(self, ballot, value, _timestamp, _source):
        if self.decide(ballot, value):
            self.send(('Agree', ballot, self._id), _source)
        else:
            self.send(('Deny', ballot, self._id), _source)

    def _event_handler_1(self, ballot, _timestamp, _source):
        val = self.staging.get(ballot)
        if (val != None):
            self.localdb[ballot] = val
        else:
            self.output('Protocol error: Committing non-existent transaction.')

    def _event_handler_2(self, ballot, _timestamp, _source):
        self.staging.pop(ballot, None)

    def decide(self, ballot, val):
        if (randint(0, 100) > self.failure_rate):
            self.staging[ballot] = val
            return True
        else:
            return False