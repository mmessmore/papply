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
Mostly things I haven't used.
.TP
My dicer is limited:  No %q.  No %t.  
.TP
No mixer
.TP
Probably many errors.  Please report.

[AUTHOR]
Michael Messmore <mike@messmore.org>

[SEE ALSO]
xapply(1), apply(1), xargs(1)
.\" vim: ft=groff
