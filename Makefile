# Base Makefile
PROG=papply

BINDIR=$(DEST)/bin

all: $(PROG) man

install: $(PROG) man
	install -m 755 $(PROG) $(BINDIR)/

man: $(PROG).man

papply.man: $(PROG) help2man.inc
	help2man -s 1 -S messmore.org -i help2man.inc -N  -o $(PROG).man --no-discard-stderr ./$(PROG)

view: $(PROG).man
	groff -Tascii -man $(PROG).man

clean:
	rm -f *.man $(PROG)

.py:
	cat $< > $@
	chmod 775 $@

.SUFFIXES: .py
