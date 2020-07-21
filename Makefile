# Copyright © 2012-2020 Jakub Wilk <jwilk@jwilk.net>
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
	# executable:
	install -d $(DESTDIR)$(bindir)
	python_exe=$$($(PYTHON) -c 'import sys; print(sys.executable)') && \
	sed \
		-e "1 s@^#!.*@#!$$python_exe@" \
		-e "s#^basedir = .*#basedir = '$(basedir)/'#" \
		$(<) > $(<).tmp
	install $(<).tmp $(DESTDIR)$(bindir)/$(<)
	rm $(<).tmp
	# library:
	install -d $(DESTDIR)$(basedir)/lib
	install -p -m644 lib/*.py $(DESTDIR)$(basedir)/lib/
ifeq "$(DESTDIR)" ""
	umask 022 && $(PYTHON) -m compileall -q $(basedir)/lib/
endif
ifeq "$(wildcard doc/*.1)" ""
	# run "$(MAKE) -C doc" to build the manpage
else
	# manual page:
	install -d $(DESTDIR)$(mandir)/man1
	install -p -m644 doc/$(<).1 $(DESTDIR)$(mandir)/man1/
endif

network =
maybe-test-net = $(and $(network),URLYCUE_TEST_NETWORK=1)

.PHONY: test
test: urlycue
	$(maybe-test-net) prove -v

.PHONY: test-installed
test-installed: $(or $(shell command -v urlycue;),$(bindir)/urlycue)
	$(maybe-test-net) URLYCUE_TEST_TARGET=urlycue prove -v

.PHONY: clean
clean:
	find . -type f -name '*.py[co]' -delete
	find . -type d -name '__pycache__' -delete
	rm -f *.tmp

.error = GNU make is required

# vim:ts=4 sts=4 sw=4 noet
