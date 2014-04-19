#!/usr/bin/env python
"""
Attempt at a drop-in replacement for KSB's excellent xapply
"""

import os
import subprocess
import sys
import argparse

MAXJOBS = 8
VERBOSE = 0

PROCTABLE = []

class Mfitter(object):
    """
    Multi-file iterator
    """
    def __init__(self, paths):
        """
        Takes:
            list of paths
        """
        self.files = []
        for path in paths:
            self.files.append(open(path, 'r'))

    def __iter__(self):
        """
        I'm my own grandpa
        """
        return self

    def reset(self):
        for mfile in self.files:
            mfile.seek(0)

    def next(self):
        """
        Returns:
            list of lines
        """
        out = []
        done = 0
        for mfile in self.files:
            try:
                out.append(mfile.next)
            except StopIteration:
                out.append("")
                done = done + 1
        if done >= len(self.files):
            raise StopIteration
        return out

def is_int(text):
    """
    Return true if s is an integer
    """
    try:
        int(text)
        return True
    except ValueError:
        return False

def dicer(intext, fmat):
    """
    Emulate KSB's dicer
    """
    diceon = 0
    select = ""
    out = ""
    field = ""
    seperator = ""
    for char in fmat:
        print "char:", char
        if char == "%":
            diceon = 1
        elif diceon == 1:
            if is_int(char):
                select = str(select) + str(char)
            elif char == "[":
                diceon = 2
            elif char == "%":
                out = out + "%"
                select = ""
                diceon = 0
            else:
                diceon = 0
                select = int(select) - 1
                out = out + intext[select] + str(char)
                select = ""
        elif diceon == 2:
            if is_int(char):
                select = str(select) + str(char)
            else:
                select = int(select) - 1
                seperator = str(char)
                diceon = 4
        elif diceon == 4:
            field = char
            diceon = 5
        elif diceon == 5:
            if is_int(char):
                field = "%d%d" % (field, char)
            elif char == "]":
                field = int(field) - int(1)
                if field < len(intext[select].split(seperator)):
                    out = str(out) + intext[select].split(seperator)[int(field)]
                diceon = 0
                field = ""
                seperator = ""
                select = ""
            else:
                out = str(out) + "%%[1%d%d%c" % (seperator, field, char)
                diceon = 0
                field = ""
                seperator = ""
                select = ""
        else:
            out = str(out) + str(char)

    if diceon == 1:
        select = int(select) - 1
        out = out + intext[select]

    return out

def pargs():
    """
    Parse Arguments
    """
    global MAXJOBS
    global VERBOSE
    parser = argparse.ArgumentParser(description="Run jobs in parallel")
    parser.add_argument('-P', '--parallel', dest='parallel', type=int,
            default=MAXJOBS,
            help='Number of parallel jobs')
    parser.add_argument('-v', '--verbose', dest='verbosity', action="count",
            default=0, help='Increase verbosity')
    parser.add_argument('-V', '--version', action='version',
            version="papply version 0.1")
    parser.add_argument('-f', '--use-file', dest='usefile',
            action='store_true', default=False)
    parser.add_argument('command')
    parser.add_argument('input',
            type=str, nargs="+",
            help='input string(s) or file(s) if -f has been specified')
    opts = parser.parse_args()

    if opts.usefile:
        opts.list = Mfitter(opts.input)
    else:
        # make a list of single item lists
        # just to have the same structure as Mfitter
        opts.list = []
        for text in opts.input:
            opts.list.append([text])

    VERBOSE = opts.verbosity
    MAXJOBS = opts.parallel

    return opts

def verbose(lvl, msg):
    """
    Print stuff based on verbosity
    """
    if VERBOSE >= lvl:
        sys.stderr.write(msg + "\n")

def startjob(cmd):
    """
    Kick off jobs in parallel
    """
    while True:
        if len(PROCTABLE) >= MAXJOBS:
            for (pid, pcmd) in PROCTABLE:
                try:
                    os.waitpid(pid, os.WNOHANG)
                except OSError:
                    PROCTABLE.remove((pid, pcmd))
                    verbose(2, "%s: finished!" % (str(pcmd)))
        else:
            break
    verbose(1, "%s: start" % (str(cmd)))
    PROCTABLE.append((subprocess.Popen(cmd, shell=True).pid, cmd))

def waitout():
    """
    Make sure all of our kids are gone
    """
    while len(PROCTABLE) > 0:
        for (pid, pcmd) in PROCTABLE:
            try:
                os.waitpid(pid, os.WNOHANG)
            except OSError:
                PROCTABLE.remove((pid, pcmd))
                verbose(2, "%s: finished!" % (str(pcmd)))

def main():
    """
    Do Stuff
    """
    opts = pargs()
    cmd = " ".join(opts.command)
    for item in opts.input:
        icmd = dicer(item, cmd)
        startjob(icmd)
    waitout()

if __name__ == '__main__':
    main()
