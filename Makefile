
PROG=papply

man: ${PROG}.man

papply.man: ${PROG} help2man.inc
	help2man -s 1 -S messmore.org -i help2man.inc -N  -o ${PROG}.man --no-discard-stderr ./${PROG}

view: ${PROG}.man
	groff -Tascii -man ${PROG}.man

clean:
	rm -f *.man
