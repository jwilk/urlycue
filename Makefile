# Copyright © 2012-2018 Jakub Wilk <jwilk@jwilk.net>
# SPDX-License-Identifier: MIT

PYTHON = python3

PREFIX = /usr/local
DESTDIR =

bindir = $(PREFIX)/bin
basedir = $(PREFIX)/share/urlycue
mandir = $(PREFIX)/share/man

.PHONY: all
all: ;

.PHONY: install
install: urlycue
	$(PYTHON) - < lib/__init__.py  # Python version check
	# binary:
	install -d $(DESTDIR)$(bindir)
	python_exe=$$($(PYTHON) -c 'import sys; print(sys.executable)') && \
	sed \
		-e "1 s@^#!.*@#!$$python_exe@" \
		-e "s#^basedir = .*#basedir = '$(basedir)/'#" \
		$(<) > $(DESTDIR)$(bindir)/$(<)
	chmod 0755 $(DESTDIR)$(bindir)/$(<)
	# library:
	install -d $(DESTDIR)$(basedir)/lib
	install -p -m644 lib/*.py $(DESTDIR)$(basedir)/lib/
ifeq "$(DESTDIR)" ""
	umask 022 && $(PYTHON) -m compileall $(basedir)/lib/
endif
ifeq "$(wildcard doc/*.1)" ""
	# run "$(MAKE) -C doc" to build the manpage
else
	# manual page:
	install -d $(DESTDIR)$(mandir)/man1
	install -p -m644 doc/$(<).1 $(DESTDIR)$(mandir)/man1/
endif

.PHONY: clean
clean:
	find . -type f -name '*.py[co]' -delete
	find . -type d -name '__pycache__' -delete

.error = GNU make is required

# vim:ts=4 sts=4 sw=4 noet
