import sys

# Minimal little argument checker
def hasArg(arg, shortArg=None):
    arg = "--" + arg
    if shortArg is not None:
        shortArg = "-" + shortArg
    for argv in sys.argv:
        if argv == arg or argv == shortArg:
            return True
    return False


def getArg(arg):
    counter = 0
    arg = "--" + arg
    for argv in sys.argv:
        counter += 1
        if argv != arg:
            continue
        if len(sys.argv) != counter:
            return sys.argv[counter]
    return None
