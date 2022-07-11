#!/usr/bin/env python
"""
Sad attempt at a drop-in replacement for KSB's excellent xapply
"""

import os
import subprocess
import signal
import sys
import argparse
import time


class Dicer(object):
    """
    Emulate KSB's dicer
    Working on de-uglying it
    """
    def __init__(self, fmat="", escape='%'):
        # just make pylint happy
        self._fmat = ""
        # making these attributes so I can refactor dice later
        self._diceon = 0
        self._select = ""

        # Our configurable escape sequence
        self.escape = escape
        # Set the format string with the setter
        self.fmat = fmat
        # Number of iterations (for %u expansion)
        self.i = 1


    def reset(self, fmat, escape):
        """
        Start over without reinstantiating
        """
        self.escape = escape
        # Set the format string with the setter
        self.fmat = fmat
        # Number of iterations (for %u expansion)
        self.i = 1

    @property
    def fmat(self):
        """
        Just return the private attribute
        """
        return self._fmat

    @fmat.setter
    def fmat(self, value):
        """
        If no format string is specified assume that we're appending a la xargs
        """
        append = False
        escape_on = False
        for char in value:
            if not escape_on:
                if char == self.escape:
                    escape_on = True
                    continue
            if char == self.escape:
                escape_on = False
                continue
            append = True

        if append:
            self._fmat = value + " " + self.escape + "1"

    def dice(self, intext):
        """
        Do the work
        """

        # keep track of state
        self._diceon = 0
        # which input stream
        self._select = ""
        # seperator character
        seperator = ""
        # which field
        field = ""

        # our output
        out = ""

        for char in self.fmat:
            if char == self.escape:
                self._diceon = 1
            elif self._diceon == 1:
                if is_int(char):
                    self._select = str(self._select) + str(char)
                elif char == "u":
                    out += str(self.i)
                    self._select = ""
                    self._diceon = 0
                elif char == "[":
                    self._diceon = 2
                elif char == self.escape:
                    out = out + self.escape
                    self._select = ""
                    self._diceon = 0
                else:
                    self._diceon = 0
                    self._select = int(self._select) - 1
                    out = out + intext[self._select].rstrip() + char
                    self._select = ""
            elif self._diceon == 2:
                if is_int(char):
                    self._select = str(self._select) + str(char)
                else:
                    self._select = int(self._select) - 1
                    seperator = str(char)
                    if char == ' ':
                        seperator = None
                    self._diceon = 4
            elif self._diceon == 4:
                field = char
                self._diceon = 5
            elif self._diceon == 5:
                if is_int(char):
                    field = "%d%d" % (field, char)
                elif char == "]":
                    field = int(field) - int(1)
                    if field < len(intext[self._select].split(seperator)):
                        text = intext[self._select].split(seperator)[int(field)]
                        out = str(out) + text.rstrip()
                    self._diceon = 0
                    field = ""
                    seperator = ""
                    self._select = ""
                else:
                    out = str(out) + "%%[1%d%d%c" % (seperator, field, char)
                    self._diceon = 0
                    field = ""
                    seperator = ""
                    self._select = ""
            else:
                out = str(out) + str(char)

        # Clean up if we end on a substitution
        if self._diceon == 1:
            self._select = int(self._select) - 1
            out = out + intext[self._select]

        self.i += 1
        return out

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

def num_cpus():
    """
    Return the number of physical CPU cores

    I intentionally don't do platform detection.  I just check to see if
    the method works, in case someone else implements the same interface.

    I don't want to think about how to do this on windows.
    """
    # This works on Linux (maybe elsewhere)
    proc_path = '/proc/cpuinfo'
    if os.path.isfile(proc_path):
        cpuinfo = open(proc_path, 'r')
        for line in cpuinfo:
            # That's a tab
            if line[0:9] == "cpu cores":
                return int(line.split(':')[1].strip())

    # This works on BSD, MacOS (maybe elsewhere)
    else:
        LOG.verbose(2, "No /proc/cpuinfo, trying sysctl")
        try:
            out = subprocess.check_output(['sysctl', 'hw.ncpu'])
        except subprocess.CalledProcessError as ex:
            # we got nothin, so we'll assume 1 core
            msg = "Could not determine number of processors: %s exited %d" % \
                (ex.cmd, ex.returncode)
            LOG.verbose(2, msg)
            return 1
        return int(out.split(':')[1].strip())


def dicer(intext, fmat, escape, i):
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
        if char == escape:
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
            elif char == escape:
                out = out + escape
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
    halp = 'Number of parallel jobs (default = number of cpu cores)'
    parser.add_argument('-P', '--parallel', dest='parallel', metavar="jobs",
            type=int, default=num_cpus(), help=halp)
    parser.add_argument('-v', '--verbose', dest='verbosity', action="count",
            default=0, help='Increase verbosity')
    parser.add_argument('-V', '--version', action='version',
            version="papply version 0.1")
    parser.add_argument('-f', '--use-file', dest='usefile',
            action='store_true', default=False)
    parser.add_argument('-a', '--escape', dest='escape', metavar='c',
            default='%', help='Escape character (default = %%)')
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
        cmd = dicer(item, opts.command, opts.escape, i)
        pjob.startjob(cmd)
    pjob.waitout()

if __name__ == '__main__':
    LOG = MLogger()
    main()
