#!/usr/bin/env python

import os
import subprocess
import sys
import argparse

MAXJOBS=8
VERBOSE=0

proctable = []

def is_int(s):
	try:
		int(s)
		return True
	except ValueError:
		return False

def dicer(intext, format):
	diceon = 0
	select = ""
	out = ""
	field = ""
	seperator =""
	for c in format:
		if c == "%":
			diceon = 1
		elif diceon == 1:
			if is_int(c):
				select = str(select) + str(c)
			elif c == "[":
				diceon = 2
			else:
				diceon = 0
				select = int(select) - 1
				out = out + intext[select] + str(c)
		elif diceon == 2:
			if is_int(c):
				select = str(select) + str(c)
			else:
				select = int(select) - 1
				seperator = str(c)
				diceon = 4
		elif diceon == 4:
			field = c
			diceon = 5
		elif diceon == 5:
			if is_int(c):
				field = "%d%d" % (field, c)
			elif c == "]":
				field = int(field) - int(1)
                                if field < len(intext[select].split(seperator)):
                                    out = str(out) + intext[select].split(seperator)[int(field)]
				diceon = 0
				field = ""
				seperator =""
				select = ""
			else:
				out = str(out) + "\%[1%d%d%c" % (seperator, field, c)
				diceon = 0
				field = ""
				seperator =""
				select = ""
		else:
			out = str(out) + str(c)

	if diceon == 1:
		select = int(select) - 1
		out = out + intext[select]

	return out

def pargs():
	global MAXJOBS
	global VERBOSE
	parser = argparse.ArgumentParser(description="Run jobs in parallel")
	parser.add_argument('-P', '--parallel', dest='parallel', type=int,
			default=MAXJOBS,
			help='Number of parallel jobs')
	parser.add_argument('-i', '--input', dest='input',
			type=argparse.FileType('r'),
			default=sys.stdin,
			help='input file (defaults to stdin)')
	parser.add_argument('-v', '--verbose', dest='verbosity', action="count",
			default=0, help='Increase verbosity')
	parser.add_argument('-V', '--version', action='version',
			version="papply version 0.1")
	parser.add_argument('command', nargs='+')
	opts = parser.parse_args()
	VERBOSE = opts.verbosity
	MAXJOBS = opts.parallel
	return opts

def verbose(lvl, msg):
	if VERBOSE >= lvl:
		sys.stderr.write(msg + "\n")

def startjob(cmd):
	global proctable
	while True:
		if len(proctable) >= MAXJOBS:
			for (pid,pcmd) in proctable:
				try:
					(id, status) = os.waitpid(pid, os.WNOHANG)
				except OSError:
					proctable.remove((pid,pcmd))
					verbose(2, "%s: finished!" % (str(pcmd)))
		else:
			break
	verbose(1,"%s: start" % (str(cmd)))
	proctable.append((subprocess.Popen(cmd, shell=True).pid, cmd))

def waitout():
	while len(proctable) > 0:
		for (pid,pcmd) in proctable:
			try:
				(id, status) = os.waitpid(pid, os.WNOHANG)
			except OSError:
				proctable.remove((pid,pcmd))
				verbose(2, "%s: finished!" % (str(pcmd)))

def main():
	opts = pargs()
	cmd = " ".join(opts.command)
	for line in opts.input:
		line = line.rstrip()
                icmd = dicer([line], cmd)
		startjob(icmd)
	waitout()



if __name__ == '__main__':
	main()
