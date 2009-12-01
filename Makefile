# -*- mode: makefile-gmake; coding: utf-8 -*-

all:

install:
	install -D -m 644 *.py $(DESTDIR)/usr/share/pyicebox
	install -D -m 644 *.ice $(DESTDIR)/usr/share/pyicebox
	ln -s /usr/share/pyicebox/Server.py $(DESTDIR)/usr/bin/pyicebox

.PHONY: clean
clean:
	find . -name "*.pyc" | xargs $(RM)
	find . -name "*~" | xargs $(RM)
