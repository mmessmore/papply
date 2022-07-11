#!/usr/bin/env python
"""
Attempt at a drop-in replacement for KSB's excellent xapply
"""

import os
import subprocess
import signal
import sys
import argparse
import time

class MLogger(object):
    """
    Do logging
    """

    def __init__(self, verbosity=0, error=sys.stderr, out=sys.stdout):
        self.verbosity = verbosity
        # grab just the name of the process, not the full path
        self.name = sys.argv[0]
        self.name = self.name.split('/')[-1]

        self.error = error
        self.out = out

    def verbose(self, level, msg):
        """
        Print a message based on verbosity
        """
        if self.verbosity > level:
            self.error.write("%s: %s\n" % (self.name, msg))

    def message(self, msg):
        """
        Unconditionallu print a message
        """
        self.out.write("%s: %s\n" % (self.name, msg))

class ParaDo(object):
    """
    Managed Parallelized Processes.

    Basically keep X number of plates spinning.
    """
    def __init__(self, maxjobs):
        """
        Takes:
            number of jobs to run in parallel
        """
        self.maxjobs = maxjobs
        self.jobs = []


    def startjob(self, cmd):
        """
        Kick off jobs in parallel
        """
        while True:
            if len(self.jobs) >= self.maxjobs:
                for (pid, pcmd) in self.jobs:
                    try:
                        os.waitpid(pid, os.WNOHANG)
                    except OSError:
                        self.jobs.remove((pid, pcmd))
                        LOG.verbose(2, "%s: finished!" % (str(pcmd)))
            else:
                break
        LOG.verbose(1, "%s" % (str(cmd)))
        self.jobs.append((subprocess.Popen(cmd, shell=True).pid, cmd))

    def waitout(self):
        """
        Make sure all of our kids are gone
        """
        while len(self.jobs) > 0:
            for (pid, pcmd) in self.jobs:
                try:
                    os.waitpid(pid, os.WNOHANG)
                except OSError:
                    self.jobs.remove((pid, pcmd))
                    LOG.verbose(2, "%s: finished!" % (str(pcmd)))

    def kill(self):
        """
        Kill off my children
        """
        shot = []

        while len(self.jobs) > 0:
            for (pid, pcmd) in self.jobs:
                try:
                    os.waitpid(pid, os.WNOHANG)
                except OSError:
                    self.jobs.remove((pid, pcmd))
                    LOG.verbose(2, "%s: finished!" % (str(pcmd)))

                # TERM then KILL each
                mysig = signal.SIGTERM
                if pid in shot:
                    mysig = signal.SIGKILL
                    LOG.verbose(2,
                            "Shooting pid %s with signal %d" % (pid, mysig))
                shot.append(pid)
                os.kill(pid, mysig)
                time.sleep(1)


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
            if path == "-":
                self.files.append(sys.stdin)
            else:
                self.files.append(open(path, 'r'))

    def __iter__(self):
        """
        I'm my own grandpa
        """
        return self

    def reset(self):
        """
        seek all inputs back to 0
        """
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
                out.append(mfile.next())
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

def dicer(intext, fmat, i):
    """
    Emulate KSB's dicer
    This is a big ugly state machine... it's needs to be better
    """
    diceon = 0
    select = ""
    out = ""
    field = ""
    seperator = ""

    for char in fmat:
        if char == "%":
            diceon = 1
        elif diceon == 1:
            if is_int(char):
                select = str(select) + str(char)
            elif char == "u":
                out += str(i)
                select = ""
                diceon = 0
            elif char == "[":
                diceon = 2
            elif char == "%":
                out = out + "%"
                select = ""
                diceon = 0
            else:
                diceon = 0
                select = int(select) - 1
                out = out + intext[select].rstrip() + char
                select = ""
        elif diceon == 2:
            if is_int(char):
                select = str(select) + str(char)
            else:
                select = int(select) - 1
                seperator = str(char)
                if char == ' ':
                    seperator = None
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
                    text = intext[select].split(seperator)[int(field)]
                    out = str(out) + text.rstrip()
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

    # Clean up if we end on a substitution
    if diceon == 1:
        select = int(select) - 1
        out = out + intext[select]

    return out

def pargs():
    """
    Parse Arguments
    """
    parser = argparse.ArgumentParser(description="Run jobs in parallel")
    parser.add_argument('-P', '--parallel', dest='parallel', type=int,
            default=8, help='Number of parallel jobs')
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

    LOG.verbosity = opts.verbosity

    return opts


def main():
    """
    Do Stuff
    """
    opts = pargs()
    pjob = ParaDo(opts.parallel)
    i = 0
    for item in opts.list:
        i += 1
        cmd = dicer(item, opts.command, i)
        pjob.startjob(cmd)
    pjob.waitout()

if __name__ == '__main__':
    LOG = MLogger()
    main()
