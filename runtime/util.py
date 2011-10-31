import multiprocessing, time, sys, traceback, os, signal, time

if not __name__ == "__main__":
    from .udp import UdpEndPoint

PerformanceCounters = {}
RootProcess = None
EndPoint = UdpEndPoint
PrintProcStats = False

def maximum(iterable):
    if (len(iterable) == 0): return -1
    else: return max(iterable)

def config_endpoint(endpoint):
    global EndPoint
    if endpoint == "udp":
        EndPoint = UdpEndPoint
    elif endpoint == "tcp":
        EndPoint = TcpEndPoint

def create_endpoint():
    if type(EndPoint) == type:
        return EndPoint()
    else:
        raise RuntimeError("Endpoint undefined before use.")

def createprocs(pcls, n, args=None):
    # if not issubclass(pcls, DistProcess):
    #     sys.stderr.write("Error: Can not create non-DistProcess.\n")
    #     return set()

    global RootProcess
    if RootProcess == None:
        if type(EndPoint) == type:
            RootProcess = EndPoint()
        else:
            sys.stderr.write("Error: EndPoint not defined.\n")

    print("Creating procs %s.."%pcls.__name__)
    pipes = []
    for i in range(n):
        (childp, ownp) = multiprocessing.Pipe()
        p = pcls(RootProcess, childp)
        pipes.append((childp, ownp))      # Buffer the pipe
        p.start()               # We need to start proc right away to obtain
                                # EndPoint for p
    print("%d instances of %s created."%(n, pcls.__name__))
    result = set()
    for childp, ownp in pipes:
        childp.close()
        cid = ownp.recv()
        cid._initpipe = ownp    # Tuck the pipe here
        result.add(cid)
    if (args != None):
        setupprocs(result, args)

    return result

def setupprocs(pids, args):
    for p in pids:
        p._initpipe.send(("setup", args))

def startprocs(procs):
    global PerformanceCounters

    init_performance_counters(procs)
    print("Starting procs...")
    for p in procs:
        p._initpipe.send("start")
        del p._initpipe

def collect_statistics():
    global PerformanceCounters
    try:
        while (True):
            src, tstamp, tup = RootProcess.recv(True)
            event_type, count = tup
            if PerformanceCounters.get(src) != None:
                PerformanceCounters[src][event_type] += count
    except Exception:
        err_info = sys.exc_info()
        print("Caught global unexpect exception:")
        traceback.printtb(err_info[2])
    except KeyboardInterrupt as e:
        pass

def config_print_individual_proc_stats(p):
    global PrintProcStats
    PrintProcStats = p

def init_performance_counters(procs):
    global PerformanceCounters
    for p in procs:
        PerformanceCounters[p] = {'sent': 0, 'unitsdone' : 0, 'totaltime' : 0,
                                  'totalusrtime' : 0, 'totalsystime' : 0,
                                  'usertime' :0 , 'systemtime' : 0,
                                  'elapsedtime' : 0}

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

def config_fail_rate(procs, failtype, rate):
    for p in procs:
        p._initpipe.send(("set_failure_rate", [failtype, rate]))

def config_sim_total_units(procs, num_units):
    for p in procs:
        p._initpipe.send(("set_total_units_to_run", [num_units]))

def config_max_event_timeout(procs, time):
    for p in procs:
        p._initpipe.send(("set_event_timeout", [time]))

def config_trace(procs, trace):
    for p in procs:
        p._initpipe.send(("set_trace", [trace]))
