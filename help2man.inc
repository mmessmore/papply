[NAME]
papply - Run templated commands (optionally) in parallel

[EXAMPLES]
Run 2 jobs in parallel based on command line input
.IP
\f(CW$ papply -P2 'echo %1' one two three four\fR
.PP
Iterate over standard input (\-)
.IP
\f(CW$ seq 1 30 | papply -f 'touch file%1' \-\fR
.PP
Operate over a colon delimited file.
.IP
\f(CW$ papply \-f 'ssh %[1:1] "mv %[1:2] %[1:3]"' hostlist\fR
.PP
Operate over multiple files at the same time
.IP
\f(CW$ papply \-f 'ln -s %1 %1"' filelist targetlist\fR

[BUGS]
There are two types of deficiencies here.  Some are on the TODO list,
others will not be implemented.  See the TODO file in the source for
planned... maybe... one day... items.
.PP
There will be no use of ptwb, gtfw, xclate or their associated options. (\-A, \-d, \-g, \-J, \-t, \-u).  Part of the mission here is to be self-contained.
.PP
No known bugs in what is supported.  Please let me know if you find them

[AUTHOR]
Michael Messmore <mike@messmore.org>

[SEE ALSO]
xapply(1), apply(1), xargs(1)
.\" vim: ft=groff
