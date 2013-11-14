# -*- mode: makefile-gmake; coding: utf-8 -*-

all:

install:
	install -d $(DESTDIR)/usr/share/pyshared/icebox/
	install -D -m 644 icebox/*.py $(DESTDIR)/usr/share/pyshared/icebox/
	install -d $(DESTDIR)/usr/share/icebox/doc/
	install -D -m 644 doc/* $(DESTDIR)/usr/share/icebox/doc/
	install -d $(DESTDIR)/usr/bin

	install -D -m 755 icebox/pyicebox $(DESTDIR)/usr/bin/

.PHONY: test
test:
	atheist -veo test

.PHONY: clean
clean:
	find . -name "*.pyc" -delete
	find . -name "*~" -delete

