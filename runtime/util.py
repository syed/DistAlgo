import multiprocessing, threading, random, time, queue, sys, traceback, os, signal, time

AllProcesses = []
PerformanceCounters = {}
PerformancePipe = multiprocessing.Queue()

def maximum(iterable):
    if (len(iterable) == 0): return -1
    else: return max(iterable)

def createprocs(pcls, n, args=None):
    global AllProcesses
    global PerformanceCounters
    global PerformancePipe

    baseidx = len(AllProcesses)
    result = [pcls(i, multiprocessing.Queue(), PerformancePipe)
                   for i in range(baseidx, baseidx + n)]
    if (args != None):
        for p in result:
            p.setup(*args)
    AllProcesses.extend(result)
    return set(range(baseidx, baseidx+n))

def setup_processes(pids, args):
    global AllProcesses
    for i in pids:
        AllProcesses[i].setup(*args)

def config_trace(trace):
    global AllProcesses
    for p in AllProcesses:
        p._trace = trace

def init_performance_counters():
    global PerformanceCounters
    for i in range(0, len(AllProcesses)):
        PerformanceCounters[i] = {'sent': 0, 'unitsdone' : 0, 'totaltime' : 0}

def start_simulation():
    global PerformanceCounters

    init_performance_counters()
    print("Starting procs...")
    for p in AllProcesses:
        p._set_all_processes(AllProcesses)
        p.start()
    try:
        while (True):
            (pid, event_type, data) = PerformancePipe.get(True)
            PerformanceCounters[pid][event_type] += data
    except Exception:
        err_info = sys.exc_info()
        print("Caught unexpect exception %s at comm thread[%d]"%
              (self._id, str(err_info[0])))
        traceback.printtb(err_info[2])
    except KeyboardInterrupt:
        pass

def print_performance_statistics(outfd):
    global PerformanceCounters

    statstr = "***** Statistics *****\n"
    tot_sent = 0
    tot_time = 0
    tot_units = 0
    for key in PerformanceCounters:
        val = PerformanceCounters[key]
        tot_sent += val['sent']
        tot_time += val['totaltime']
        tot_units += val['unitsdone']
        statstr += ("### Process %d: \n" % key)
        statstr += ("\tTotal messages sent: %d\n" % val['sent'])
        if (val['unitsdone'] > 0):
            statstr += ("\tAverage message per work unit: %f\n" %
                        (val['sent']/val['unitsdone']))
            statstr += ("\tAverage time per work unit: %f\n" %
                        (val['totaltime']/val['unitsdone']))
    if (tot_units > 0):
        statstr += ("*** Overall average messages per unit: %f\n"
                    % (tot_sent/tot_units))
        statstr += ("*** Overall average time per unit: %f\n"
                    % (tot_time/tot_units))

    outfd.write(statstr)

def config_fail_rate(failtype, rate):
    for p in AllProcesses:
        p.set_failure_rate(failtype, rate)

def config_sim_total_units(num_units):
    for p in AllProcesses:
        p.set_total_units_to_run(num_units)

def config_max_event_timeout(time):
    for p in AllProcesses:
        p.set_event_timeout(time)

