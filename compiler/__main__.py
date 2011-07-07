"""Main entry point"""

import sys
if sys.argv[0].endswith("__main__.py"):
    sys.argv[0] = "python -m disalgo"


def parseArgs(argv):
    if (len(argv) < 2):
        printUsage(argv[0])
        sys.exit(1)

    printsource = False
    optimize = False
    sourcefile = None
    run = False
    for arg in argv:
        if (arg == "-p"):
            printsource = True
        elif (arg == "-o"):
            optimize = True
        elif (arg == "-r"):
            run = True
        else:
            sourcefile = arg
    return (sourcefile, printsource, optimize, run)

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
    (infilename, ps, opt, r) = parseArgs(sys.argv)

    infd = open(infilename, 'r')
    pytree = dist_compile(infd)
    infd.close()

    pysource = to_source(pytree)

    outfile = infilename[:-4] + ".py"
    outfd = open(outfile, 'w')
    outfd.write(pysource)
    outfd.close()

    sys.exit(0)

if __name__ == '__main__':
    main()
