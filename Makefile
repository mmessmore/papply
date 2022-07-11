# Base Makefile
PROG=papply
DEST?=$(HOME)

BINDIR=$(DEST)/bin
MANDIR=$(DEST)/man/man1

DIRS=$(BINDIR) $(MANDIR)

.SUFFIXES: .py

all: $(PROG) man

install: $(DIRS) $(PROG) man
	install -m 755 $(PROG) $(BINDIR)/
	install -m 644 $(PROG).man $(MANDIR)/$(PROG).1

deinstall:
	rm -f $(BINDIR)/$(PROG)
	rm -f $(MANDIR)/$(PROG).1

$(DIRS):
	install -d $@

man: $(PROG).man

papply.man: $(PROG) help2man.inc
	help2man -s 1 -S messmore.org -I help2man.inc -N -o $(PROG).man --no-discard-stderr ./$(PROG)

view: $(PROG).man
	groff -Tascii -man $(PROG).man

clean:
	rm -f *.man $(PROG) *.pyc

lint:
	pylint --rcfile=pylint.rc $(PROG).py

.py:
	cat $< > $@
	chmod 775 $@

