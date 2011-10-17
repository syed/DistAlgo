import multiprocessing, threading, random, time, queue, sys, traceback, os, signal, time

AllProcesses = []
PerformanceCounters = {}
PerformancePipe = multiprocessing.Queue()
PrintProcStats = False

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

def config_print_individual_proc_stats(p):
    global PrintProcStats
    PrintProcStats = p

def init_performance_counters():
    global PerformanceCounters
    for i in range(0, len(AllProcesses)):
        PerformanceCounters[i] = {'sent': 0, 'unitsdone' : 0, 'totaltime' : 0,
                                  'totalusrtime' : 0, 'totalsystime' : 0,
                                  'usertime' :0 , 'systemtime' : 0,
                                  'elapsedtime' : 0}

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
            if PerformanceCounters.get(pid) != None:
                PerformanceCounters[pid][event_type] += data
    except Exception:
        err_info = sys.exc_info()
        print("Caught global unexpect exception:")
        traceback.printtb(err_info[2])
    except KeyboardInterrupt:
        pass

def print_performance_statistics(outfd):
    global PerformanceCounters

    statstr = "***** Statistics *****\n"
    tot_sent = 0
    tot_usrtime = 0
    tot_systime = 0
    tot_time = 0
    tot_units = 0
    for key, val in PerformanceCounters.items():
        tot_sent += val['sent']
        tot_usrtime += val['totalusrtime']
        tot_systime += val['totalsystime']
        tot_time += val['totaltime']
        tot_units += val['unitsdone']
        if PrintProcStats:
            statstr += ("### Process %d: \n" % key)
            statstr += ("\tTotal messages sent: %d\n" % val['sent'])
            statstr += ("\tTotal usertime: %f\n" % val['usertime'])
            statstr += ("\tTotal systemtime: %f\n" % val['systemtime'])
            statstr += ("\tTotal time: %f\n" % val['elapsedtime'])
            if (val['unitsdone'] > 0):
                statstr += ("\tAverage messages per work unit: %f\n" %
                            (val['sent']/val['unitsdone']))
                statstr += ("\tAverage elapsed time per work unit: %f\n" %
                            (val['totaltime']/val['unitsdone']))

    statstr += ("* Total procs: %d\n" % len(PerformanceCounters))
    statstr += ("*** Total usertime: %f\n" % tot_usrtime)
    statstr += ("*** Total systemtime: %f\n" % tot_systime)
    statstr += ("*** Average usertime: %f\n" % (tot_usrtime/len(PerformanceCounters)))
    statstr += ("*** Average time: %f\n" % ((tot_usrtime + tot_systime)/len(PerformanceCounters)))

    if (tot_units > 0):
        statstr += ("*** Overall average messages per unit: %f\n"
                    % (tot_sent/tot_units))
        statstr += ("*** Overall average usertime per unit: %f\n"
                    % (tot_usrtime/tot_units))
        statstr += ("*** Overall average systime per unit: %f\n"
                    % (tot_systime/tot_units))
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

