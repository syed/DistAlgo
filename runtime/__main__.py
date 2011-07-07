import sys, stat, os
from compiler import *
from .util import *
from .event import *

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
    

def main():
    global source_dir

    target = parseArgs(sys.argv)
    if not target.endswith(".run"):
        die("Expecting a run file as input.")

    source_dir = os.path.dirname(target)
    purename = os.path.basename(target)[:-4]

    targetfd = open(target, "r")
    statsfile = purename + ".out"
    statsfd = open(statsfile, "w")

    exec(targetfd.read(), globals())
    targetfd.close()

    config()
    start_simulation()
    print_performance_statistics(statsfd)

def eval_source(distsrc, pysrc):
    global DistProcess
    distmode, pymode, codeobj = None, None, None
    try:
        distmode = os.stat(distsrc)
    except OSError:
        die("DistAlgo source not found.")

    try:
        pymode = os.stat(pysrc)
        if pymode[stat.ST_MTIME] >= distmode[stat.ST_MTIME]:
            pyfd = open(pysrc, 'r')
            codeobj = pyfd.read()
            pyfd.close()
    except OSError:
        pass

    if codeobj == None:
        distfd = open(distsrc, 'r')
        codeobj = dist_compile_to_string(distfd)
        distfd.close()

    exec(codeobj, globals())

def die(str):
    print(str)
    sys.exit(1)

if __name__ == '__main__':
    main()
