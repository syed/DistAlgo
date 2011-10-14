"""Main entry point"""

import sys
import time
if sys.argv[0].endswith("__main__.py"):
    sys.argv[0] = "python -m disalgo"

args = dict()

def parseArgs(argv):
    if (len(argv) < 2):
        printUsage(argv[0])
        sys.exit(1)

    global args
    args['printsource'] = False
    args['optimize'] = False
    args['sourcefile'] = None
    args['run'] = False
    args['full'] = False
    for arg in argv:
        if (arg == "-p"):
            args['printsource'] = True
        elif (arg == "-o"):
            args['optimize'] = True
        elif (arg == "-r"):
            args['run'] = True
        elif (arg == "-F" or arg == "--full"):
            args['full'] = True
        else:
            args['sourcefile'] = arg

def printUsage(name):
    usage = """
Usage: %s [-p] [-o] <infile>
     where <infile> is the file name of the distalgo source
"""
    sys.stderr.write(usage % name)

import ast

from .dist import DistalgoTransformer
from .codegen import to_source
from .compiler import dist_compile

def main():
    parseArgs(sys.argv)

    start = time.time()
    infd = open(args['sourcefile'], 'r')
    pytree = dist_compile(infd)
    infd.close()
    elapsed = time.time() - start

    pysource = to_source(pytree)

    outfile = args['sourcefile'][:-4] + ".py"
    outfd = open(outfile, 'w')
    outfd.write(pysource)
    outfd.close()

    print("Total compilation time: %f second(s)." % elapsed)
    sys.exit(0)

if __name__ == '__main__':
    main()
