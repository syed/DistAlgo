class Proposer(DistProcess):

    def __init__(self, pid, pipe, perf_pipe):
        DistProcess.__init__(self, pid, pipe, perf_pipe)
        self._event_patterns = [EventPattern(Event.receive, 'Promise', [], [(1, 'propNum'), (2, 'vp'), (3, 'vv'), (4, 'a')], [self._receive_handler_0]), EventPattern(Event.receive, 'Accept', [], [(1, 'propNum'), (2, 'propVal'), (3, 'a')], [self._receive_handler_1])]
        self._sent_patterns = []
        self._label_events = {'propose': self._event_patterns, 'reinit': self._event_patterns, 'prepare': self._event_patterns}
        self._receive_messages_0 = set()
        self._receive_messages_1 = set()

    def setup(self, acceptors, totprocs, quorum):
        self.acpts = acceptors
        self.nprocs = totprocs
        self.maj = quorum
        (self.propNum, self.propVal) = (self._id, self._id)

    def main(self):
        while True:
            self._label_('prepare')
            self.send(('Prepare', self.propNum, self._id), self.acpts)
            __await_timer_1 = time.time()
            _timeout = False
            while (not (len(self._has_receive_0(self.propNum)) > self.maj)):
                self._process_event_(self._event_patterns, True)
                if (time.time() - (__await_timer_1) > TIMEOUT):
                    _timeout = True
                    break
            self._label_('propose')
            if (not _timeout):
                safeval = (-1)
                if (len(self._has_receive_0(self.propNum)) > 0):
                    (_, safeval, _) = max(self._has_receive_0(self.propNum))
                if (safeval >= 0):
                    self.propVal = safeval
                self.send(('Propose', self.propNum, self.propVal, self._id), self.acpts)
                __await_timer_2 = time.time()
                _timeout = False
                while (not (len(self._has_receive_1(self.propNum, self.propVal)) > self.maj)):
                    self._process_event_(self._event_patterns, True)
                    if (time.time() - (__await_timer_2) > TIMEOUT):
                        _timeout = True
                        break
                if (not _timeout):
                    self.output('Succeeded in proposing %d' % (self.propVal))
                    return 
            self._label_('reinit')
            self.output('Failed ballot %d, retrying.' % (self.propNum))
            self.propNum = self.next_prop_num()

    def next_prop_num(self):
        return self.propNum + (self.nprocs)

    def _receive_handler_0(self, _propNum, _vp, _vv, _a, _timestamp, _source):
        self._receive_messages_0.add((_propNum, _vp, _vv, _a))

    def _has_receive_0(self, propNum):
        return [(vp_, vv_, a_) for (propNum_, vp_, vv_, a_) in self._receive_messages_0 if (propNum_ == propNum)]

    def _receive_handler_1(self, _propNum, _propVal, _a, _timestamp, _source):
        self._receive_messages_1.add((_propNum, _propVal, _a))

    def _has_receive_1(self, propNum, propVal):
        return [a_ for (propNum_, propVal_, a_) in self._receive_messages_1 if (propNum_ == propNum) if (propVal_ == propVal)]


class Acceptor(DistProcess):

    def __init__(self, pid, pipe, perf_pipe):
        DistProcess.__init__(self, pid, pipe, perf_pipe)
        self._event_patterns = [EventPattern(Event.send, 'Promise', [], [(1, '_pn'), (2, '_vpn'), (3, '_vv'), (4, 'self')], [self._send_handler_0]), EventPattern(Event.send, 'Accept', [], [(1, '_vpn'), (2, '_vv'), (3, 'self')], [self._send_handler_1]), EventPattern(Event.receive, 'Prepare', [], [(1, 'n'), (2, 'p')], [self._event_handler_2]), EventPattern(Event.receive, 'Propose', [], [(1, 'n'), (2, 'v'), (3, 'p')], [self._event_handler_3])]
        self._sent_patterns = []
        self._label_events = {}
        self._send_messages_0 = set()
        self._send_messages_1 = set()

    def setup(self):
        pass

    def main(self):
        while (not False):
            self._process_event_(self._event_patterns, True)

    def _event_handler_2(self, n, p, _timestamp, _source):
        if ((len(self._has_send_0()) == 0) or (n > max(self._has_send_0()[0]))):
            if (len(self._has_send_1()) > 0):
                (maxpn, votedval, _) = max(self._has_send_1())
                self.send(('Promise', n, maxpn, votedval, self._id), p)
            else:
                self.send(('Promise', n, (-1), (-1), self._id), p)

    def _event_handler_3(self, n, v, p, _timestamp, _source):
        if ((len(self._has_send_0()) == 0) or (n >= max(self._has_send_0()[0]))):
            self.send(('Accept', n, v, self._id), p)

    def _send_handler_0(self, __pn, __vpn, __vv, _self, _timestamp, _source):
        self._send_messages_0.add((__pn, __vpn, __vv, _self))

    def _has_send_0(self):
        return [(_pn_, _vpn_, _vv_, self_) for (_pn_, _vpn_, _vv_, self_) in self._send_messages_0]

    def _send_handler_1(self, __vpn, __vv, _self, _timestamp, _source):
        self._send_messages_1.add((__vpn, __vv, _self))

    def _has_send_1(self):
        return [(_vpn_, _vv_, self_) for (_vpn_, _vv_, self_) in self._send_messages_1]