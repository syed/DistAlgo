class Proposer(DistProcess):

    def __init__(self, pid, pipe, perf_pipe):
        DistProcess.__init__(self, pid, pipe, perf_pipe)
        self._event_patterns = [EventPattern(Event.receive, 'Promise', [], [(1, 'propNum'), (2, '_vp'), (3, '_vv'), (4, '_a')], [self._receive_handler_0]), EventPattern(Event.receive, 'TwoAv', [], [(1, 'propNum'), (2, 'propVal'), (3, 'a')], [self._receive_handler_1])]
        self._sent_patterns = []
        self._label_events = {'propose': self._event_patterns, 'reinit': self._event_patterns, 'prepare': self._event_patterns}
        self._receive_messages_0 = set()
        self._receive_messages_1 = set()

    def setup(self, acceptors, nps, quorumSize, tolerance):
        self.acpts = acceptors
        self.total_procs = nps
        self.maj = quorumSize
        self.f = tolerance
        self.propNum = self._id
        self.propVal = self._id

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
                props = [(n, v) for (n, v, _) in self._has_receive_0(self.propNum) if (len(self._has_receive_01(self.propNum, n, v)) > self.f)]
                if (len(props) > 0):
                    (_, safeval) = max(props)
                if (safeval >= 0):
                    self.propVal = safeval
                self.send(('OneC', self.propNum, self.propVal, self._id), self.acpts)
                while (not len((self._has_receive_1(self.propNum, self.propVal) > self.maj), TIMEOUT)):
                    self._process_event_(self._event_patterns, True)
                if (not _timeout):
                    return 
            self._label_('reinit')
            self.output('Failed ballot %d, retrying.' % (self.propNum))
            self.propNum = self.next_prop_num()

    def next_prop_num(self):
        return self.propNum + (self.total_procs)

    def _receive_handler_0(self, _propNum, __vp, __vv, __a, _source):
        self._receive_messages_0.add((_propNum, __vp, __vv, __a))

    def _has_receive_0(self, propNum):
        return [(_vp_, _vv_, _a_) for (propNum_, _vp_, _vv_, _a_) in self._receive_messages_0 if (propNum_ == propNum)]

    def _has_receive_01(self, propNum, n, v):
        return [a_ for (propNum_, n_, v_, a_) in self._receive_messages_0 if (propNum_ == propNum) if (n_ == n) if (v_ == v)]

    def _receive_handler_1(self, _propNum, _propVal, _a, _source):
        self._receive_messages_1.add((_propNum, _propVal, _a))

    def _has_receive_1(self, propNum, propVal):
        return [a_ for (propNum_, propVal_, a_) in self._receive_messages_1 if (propNum_ == propNum) if (propVal_ == propVal)]


class Acceptor(DistProcess):

    def __init__(self, pid, pipe, perf_pipe):
        DistProcess.__init__(self, pid, pipe, perf_pipe)
        self._event_patterns = [EventPattern(Event.send, 'TwoAv', [], [(1, '_vpn'), (2, '_vv'), (3, 'self')], [self._send_handler_0]), EventPattern(Event.send, 'Promise', [], [(1, 'pn'), (2, 'vp'), (3, 'vv'), (4, 'a')], [self._send_handler_1]), EventPattern(Event.receive, 'Promise', [], [(1, 'propNum'), (2, 'vp'), (3, 'vv'), (4, 'a1')], [self._receive_handler_2]), EventPattern(Event.receive, 'Prepare', [], [(1, 'n'), (2, 'p')], [self._event_handler_3]), EventPattern(Event.receive, 'OneC', [], [(1, 'n'), (2, 'v'), (3, 'p')], [self._event_handler_4]), EventPattern(Event.receive, 'TwoAv', [], [(1, 'propnum'), (2, 'propval'), (3, 'p')], [self._event_handler_5])]
        self._sent_patterns = []
        self._label_events = {}
        self._send_messages_0 = set()
        self._send_messages_1 = set()
        self._receive_messages_2 = set()

    def setup(self, allprocs, quorumSize, tolerence):
        self.peers = allprocs
        self.maj = quorumSize
        self.f = tolerence

    def main(self):
        while (not False):
            self._process_event_(self._event_patterns, True)

    def _event_handler_3(self, n, p, _source):
        if (n > self.maxpromised()):
            if (len(self._has_send_0()) > 0):
                (maxpn, votedval, _) = max(self._has_send_0())
                self.send(('Promise', n, maxpn, votedval, self._id), self.peers)
            else:
                self.send(('Promise', n, (-1), (-1), self._id), self.peers)

    def _event_handler_4(self, n, v, p, _source):
        if ((n >= self.maxpromised()) and self.islegal(n, v) and (len(self._has_send_01(n)) == 0)):
            self.send(('TwoAv', n, v, self._id), self.peers)
            self.output('Sent 2av for %d in ballot %d' % ((v, n)))

    def _event_handler_5(self, propnum, propval, p, _source):
        pass

    def maxpromised(self):
        pns = self._has_send_1()
        if (len(pns) == 0):
            return (-1)
        else:
            (maxpn, _, _, _) = max(pns)
            return maxpn

    def islegal(self, propNum, propVal):
        props = [(n, v) for (n, v, _) in self._has_receive_2(propNum) if (len(self._has_receive_21(propNum, n, v)) > self.f)]
        if (len(props) > 0):
            (_, safeval) = max(props)
            if ((safeval == (-1)) or (propVal == safeval)):
                return True
            else:
                return False
        else:
            return False

    def _send_handler_0(self, __vpn, __vv, _self, _source):
        self._send_messages_0.add((__vpn, __vv, _self))

    def _has_send_0(self):
        return [(_vpn_, _vv_, self_) for (_vpn_, _vv_, self_) in self._send_messages_0]

    def _has_send_01(self, n):
        return [(_v_, self_) for (n_, _v_, self_) in self._send_messages_0 if (n_ == n)]

    def _send_handler_1(self, _pn, _vp, _vv, _a, _source):
        self._send_messages_1.add((_pn, _vp, _vv, _a))

    def _has_send_1(self):
        return [(pn_, vp_, vv_, a_) for (pn_, vp_, vv_, a_) in self._send_messages_1]

    def _receive_handler_2(self, _propNum, _vp, _vv, _a1, _source):
        self._receive_messages_2.add((_propNum, _vp, _vv, _a1))

    def _has_receive_2(self, propNum):
        return [(vp_, vv_, a1_) for (propNum_, vp_, vv_, a1_) in self._receive_messages_2 if (propNum_ == propNum)]

    def _has_receive_21(self, propNum, n, v):
        return [a2_ for (propNum_, n_, v_, a2_) in self._receive_messages_2 if (propNum_ == propNum) if (n_ == n) if (v_ == v)]