# -*- mode: makefile-gmake; coding: utf-8 -*-

all:

install: DEST=$(DESTDIR)/usr/share/pyicebox
install:
	install -D -m 644 *.py $(DEST)
	install -D -m 644 *.ice $(DEST)
	install -D -m 644 icebox.config $(DEST)
	chmod a+x $(DEST)/Server.py

#	# FIXME: use a relative path
	ln -s /usr/share/pyicebox/Server.py $(DESTDIR)/usr/bin/pyicebox

.PHONY: clean
clean:
	find . -name "*.pyc" -delete
	find . -name "*~" -delete

