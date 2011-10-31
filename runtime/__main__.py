import sys, stat, os
from compiler import *
from .util import *
from .event import *
from .sim import DistProcess

def parseArgs(argv):
    if (len(argv) < 2):
        printUsage(argv[0])
        sys.exit(1)

    sourcefile = argv[1]
    return sourcefile

source_dir = ""

def dist_source(filename):
    global source_dir
    if not filename.endswith(".dis"):
        die("DistAlgo source file should end with '.dis'")

    purename = filename[:-4]
    distsource = filename
    pysource = purename + ".py"

    eval_source(os.path.join(source_dir, distsource),
                os.path.join(source_dir, pysource))

def libmain():
    global source_dir

    target = parseArgs(sys.argv)
    if not (target.endswith(".run") or target.endswith(".dis")):
        die("Expecting a DistAlgo source or run file as input.")

    source_dir = os.path.dirname(target)
    purename = os.path.basename(target)[:-4]

    targetfd = open(target, "r")
    statsfile = purename + ".out"
    statsfd = open(statsfile, "w")

    exec(targetfd.read(), globals())
    targetfd.close()

    main()

    collect_statistics()
    print_performance_statistics(statsfd)

def eval_source(distsrc, pysrc):
    distmode, pymode, codeobj = None, None, None
    try:
        distmode = os.stat(distsrc)
    except OSError:
        die("DistAlgo source not found.")

    try:
        pymode = os.stat(pysrc)
    except OSError:
        pymode = None

    if pymode == None or pymode[stat.ST_MTIME] < distmode[stat.ST_MTIME]:
        distfd = open(distsrc, 'r')
        pyfd = open(pysrc, 'w+')
        dist_compile_to_file(distfd, pyfd)
        distfd.close()
        pyfd.close()

    pyfd = open(pysrc, 'r')
    code = compile(''.join(pyfd.readlines()), pysrc, 'exec')
    exec(code, globals())
    pyfd.close()

def die(mesg = None):
    if mesg != None:
        sys.stderr.write(mesg + "\n")
    sys.exit(1)

if __name__ == '__main__':
    libmain()
