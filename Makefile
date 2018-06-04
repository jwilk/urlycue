# Copyright © 2012-2018 Jakub Wilk <jwilk@jwilk.net>
# SPDX-License-Identifier: MIT

PYTHON = python3
INSTALL = $(if $(shell command -v ginstall;),ginstall,install)

PREFIX = /usr/local
DESTDIR =

exe = urlycue

bindir = $(PREFIX)/bin
basedir = $(PREFIX)/share/$(exe)
mandir = $(PREFIX)/share/man

.PHONY: all
all: ;

.PHONY: install
install:
	# binary:
	$(INSTALL) -d -m755 $(DESTDIR)$(bindir)
	python_exe=$$($(PYTHON) -c 'import sys; print(sys.executable)') && \
	sed \
		-e "1 s@^#!.*@#!$$python_exe@" \
		-e "s#^basedir = .*#basedir = '$(basedir)/'#" \
		$(exe) > $(DESTDIR)$(bindir)/$(exe)
	chmod 0755 $(DESTDIR)$(bindir)/$(exe)
	# library:
	( find lib -type f ! -name '*.py[co]' ) \
	| xargs -t -I {} $(INSTALL) -p -D -m644 {} $(DESTDIR)$(basedir)/{}
ifeq "$(wildcard doc/$(exe).1)" ""
	# run "$(MAKE) -C doc" to build the manpage
else
	# manual page:
	$(INSTALL) -p -D -m644 doc/$(exe).1 $(DESTDIR)$(mandir)/man1/$(exe).1
endif

.PHONY: clean
clean:
	find . -type f -name '*.py[co]' -delete
	find . -type d -name '__pycache__' -delete

.error = GNU make is required

# vim:ts=4 sts=4 sw=4 noet
