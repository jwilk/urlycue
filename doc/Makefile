# Copyright © 2014-2017 Jakub Wilk <jwilk@jwilk.net>
# SPDX-License-Identifier: MIT

export LC_ALL=C

rst2man = $(or $(shell which rst2man),rst2man.py)
exe = urlycue

.PHONY: all
all: $(exe).1

$(exe).1: manpage.rst
	$(rst2man) --input-encoding=UTF-8 < $(<) > $(@).tmp
	perl -pi -e '/^[.]BI\b/ and s/\\fP/\\fR/g' $(@).tmp  # work-around for https://bugs.debian.org/806601
	mv $(@).tmp $(@)

.PHONY: clean
clean:
	rm -f $(exe).1 *.tmp

# vim:ts=4 sts=4 sw=4 noet
