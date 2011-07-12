import multiprocessing, threading, random, time, queue, sys, traceback, os, signal, time
from .event import *

class DistProcess(multiprocessing.Process):
    # ====================
    # Each Process will have one 'Comm' thread
    # ====================
    class Comm(threading.Thread):
        def __init__(self, pid, queue, parent):
            threading.Thread.__init__(self)
            self._id = pid
            self._p = parent
            self._queue = queue  # Queue used to communicate with our main Site
                                # process
            self._running = True

        def run(self):
            try:
                while self._running:
                    (src, clock, data) = self._p.receive()
                    self._queue.put(Event(Event.receive, src, clock, data))
            except Exception as e:
                traceback.print_tb(e.__traceback__)
                err_info = sys.exc_info()
                print("Caught unexpected exception %s at comm thread[%d]"%
                       (self._id, str(err_info[0])))
                traceback.printtb(err_info[2])
            except KeyboardInterrupt:
                pass

    def __init__(self, pid, pipe, perf_pipe):
        multiprocessing.Process.__init__(self)
        self._id = pid
        self._pipe = pipe
        self._perf_pipe = perf_pipe
        self._event_queue = queue.Queue() # Queue used to communicate with Comm
        self._comm = DistProcess.Comm(pid, self._event_queue, self)
        self._running = True

        self._logical_clock = 0

        self._event_patterns = []
        self._received_q = []
        self._label_events = {}
        self._event_backlog = []
        self._failures = {'send': 0,
                          'receive': 0,
                          'crash': 0}
        self._evtimeout = None

        # Performance counters:
        self._total_units = -1
        self._current_units = 0

        self._trace = False

    def term_handler(self):
        print("C-%d Terminating..." % self._id)
        sys.exit(1)

    def run(self):
        self._comm.start()
        try:
            self._totusrtime_start, self._totsystime_start, _, _, _ = os.times()
            self._tottime_start = time.clock()
            self.main()
        except Exception as e:
            print("Unexpected error at process %d:%s"% (self._id, str(e)))
            traceback.print_tb(e.__traceback__)
        except KeyboardInterrupt:
            pass

    def _set_all_processes(self, procs):
        self._allprocs = procs

    def output(self, message):
        print("%s[%d]: %s"%(self.__class__.__name__, self._id, message))

    # Wrapper functions for message passing:
    def send(self, data, to):
        if (self._fails('send')):
            return False

        message = (self._id, self._logical_clock, data)

        if (hasattr(to, '__iter__')):
            for t in to:
                if (isinstance(t, int)):
                    self._allprocs[t]._pipe.put(message)
                    self._perf_pipe.put((self._id, 'sent', 1))
                elif (isinstance(t, DistProcess)):
                    t._pipe.put(message)
                    self._perf_pipe.put((self._id, 'sent', 1))
        elif (isinstance(to, int)):
            self._allprocs[to]._pipe.put(message)
            self._perf_pipe.put((self._id, 'sent', 1))
        elif (isinstance(to, DistProcess)):
            to._pipe.put(message)
            self._perf_pipe.put((self._id, 'sent', 1))
        else:
            return False
        if (self._trace):
            self.output("Sent %s"%str(message))
        self._event_queue.put(Event(Event.send, self._id, self._logical_clock,
                                    data))
        return True

    def receive(self):
        while (self._fails('receive')):
            self._pipe.get()
        return self._pipe.get()

    # This simulates the controlled "label" mechanism. Currently we simply
    # handle one event on one label call:
    def _label_(self, name, block=False):
        if (name.endswith("start")):
            self._begin_work_unit()
        elif (name.endswith("end")):
            self._end_work_unit()
        if (self._fails('crash')):
            self.output("Stuck in label: %s" % name)
            self._comm.join()   # This will hang our process forever
        if not name in self._label_events:
            # Error: invalid label name
            return
        self._process_event_(self._label_events[name], block)

    def _fails(self, failtype):
        if not failtype in self._failures.keys():
            return False
        if (random.randint(0, 100) < self._failures[failtype]):
            return True
        return False

    # Retrieves one message, then process the backlog event queue. 'block'
    # indicates whether to block waiting for next message to come in if the
    # queue is currently empty:
    def _process_event_(self, patterns, block):
        try:
            # Fetch one event from queue
            event = self._event_queue.get(block, self._evtimeout)
            # The following loop does a "prematch" for this new event. If it
            # matches something then we keep it. Otherwise we know there is no
            # handler for this event and thus we simply discard it.
            for p in self._event_patterns:
                if (p.match(event)):
                    self._event_backlog.append(event)
                    break
        except queue.Empty:
            pass

        unhandled = []
        for e in self._event_backlog:
            ishandled = False
            for p in patterns:
                if (p.match(e)): # Match and handle
                    # Match success, update logical clock, call handlers
                    self._logical_clock = max(self._logical_clock, e.timestamp)+1

                    args = []
                    for (index, name) in p.var:
                        args.append(event.data[index])
                    args.append(e.timestamp)
                    args.append(e.source)
                    for h in p.handlers:
                        h(*args)
                    ishandled = True

            if (not ishandled):
                unhandled.append(e)
        self._event_backlog = unhandled

    def _begin_work_unit(self):
        if (self._current_units == self._total_units):
            self.output("Reached designated work unit count.")
            usrtime, systime, _, _, _ = os.times()
            self._perf_pipe.put((self._id, 'totalusrtime',
                                 usrtime - self._totusrtime_start))
            self._perf_pipe.put((self._id, 'totalsystime',
                                 systime - self._totsystime_start))
            self._perf_pipe.put((self._id, 'totaltime',
                                 time.clock() - self._tottime_start))
            self._forever_message_loop()

        self._time_unit_start = (os.times(), time.clock())

    def _end_work_unit(self):
        usrtime_end, systime_end, _, _ ,_ = os.times()
        tottime_end = time.clock()
        ((usrtime_start, systime_start, _, _, _), tottime_start) = \
            self._time_unit_start

        self._current_units += 1
        self._perf_pipe.put((self._id, 'unitsdone', 1))
        self._perf_pipe.put((self._id, 'usertime',
                             usrtime_end - usrtime_start))
        self._perf_pipe.put((self._id, 'systemtime',
                             systime_end - systime_start))
        self._perf_pipe.put((self._id, 'elapsedtime',
                             tottime_end - tottime_start))

    def _forever_message_loop(self):
        while (True):
            self._process_event_(self._event_patterns, True)

    def _has_received(self, mess):
        try:
            self._received_q.remove(mess)
            return True
        except ValueError:
            return False

    def __str__(self):
        return "" + self._id

    def set_failure_rate(self, failtype, rate):
        self._failures[failtype] = rate

    def set_total_units_to_run(self, nunits):
        self._total_units = nunits

    def set_event_timeout(self, time):
        self._evtimeout = time

    # Simulate work, waste some random amount of time:
    def work(self):
        #time.sleep(random.randint(1, 5))
        pass

    def logical_clock(self):
        return self._logical_clock

    def incr_logical_clock(self):
        self._logical_clock += 1
