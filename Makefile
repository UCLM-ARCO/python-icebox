# -*- mode: makefile-gmake; coding: utf-8 -*-

SLICES = Process.ice

vpath %.ice /usr/share/slice/Ice

all: $(SLICES:)

%.ice:
	slice2cpp

.PHONY: clean
clean:
	find . -name "*.pyc" | xargs $(RM)
	find . -name "*~" | xargs $(RM)
