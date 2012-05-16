# -*- mode: makefile-gmake; coding: utf-8 -*-

all:

install:
	install -d $(DESTDIR)/usr/share/pyshared/icebox/
	install -D -m 644 src/*.py $(DESTDIR)/usr/share/pyshared/icebox/
	install -d $(DESTDIR)/usr/share/icebox/doc/
	install -D -m 644 doc/* $(DESTDIR)/usr/share/icebox/doc/
	install -d $(DESTDIR)/usr/bin

	install -D -m 755 src/pyicebox $(DESTDIR)/usr/bin/

.PHONY: clean
clean:
	find . -name "*.pyc" -delete
	find . -name "*~" -delete

