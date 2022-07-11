# Base Makefile
PROG=papply
DEST=~

BINDIR=$(DEST)/bin
MANDIR=$(DEST)/man/man1

DIRS=$(BINDIR) $(MANDIR)

.SUFFIXES: .py

all: $(PROG) man

install: $(DIRS) $(PROG) man
	install -m 755 $(PROG) $(BINDIR)/
	install -m 755 $(PROG).man $(MANDIR)

deinstall:
	rm -f $(BINDIR)/$(PROG)
	rm -f $(MANDIR)/$(PROG).man

$(DIRS):
	install -d $@

man: $(PROG).man

papply.man: $(PROG) help2man.inc
	help2man -s 1 -S messmore.org -i help2man.inc -N  -o $(PROG).man --no-discard-stderr ./$(PROG)

view: $(PROG).man
	groff -Tascii -man $(PROG).man

clean:
	rm -f *.man $(PROG) *.pyc

lint:
	pylint --rcfile=pylint.rc $(PROG).py

.py:
	cat $< > $@
	chmod 775 $@

