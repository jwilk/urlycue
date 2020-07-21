#!/usr/bin/env bash

# Copyright © 2020 Jakub Wilk <jwilk@jwilk.net>
# SPDX-License-Identifier: MIT

set -e -u
echo 1..4
base="${0%/*}/.."
prog=${URLYCUE_TEST_TARGET:-"$base/urlycue"}
if [[ -z ${URLYCUE_TEST_NETWORK-} ]]
then
    echo 'URLYCUE_TEST_NETWORK is not set' >&2
    printf 'not ok %d\n' {1..4}
    exit 1
fi
out=$("$prog" "$base/doc/README")
sed -e 's/^/# /' <<< "$out"
echo ok 1
out=$("$prog" <<< 'https://expired.badssl.com/')
sed -e 's/^/# /' <<< "$out"
case $out in
    '<stdin>:1: ['*'[SSL: CERTIFICATE_VERIFY_FAILED]'*'] https://expired.badssl.com/')
        echo ok 2;;
    *)
        echo not ok 2;;
esac
out=$("$prog" <<< 'https://wrong.host.badssl.com/')
sed -e 's/^/# /' <<< "$out"
case $out in
    '<stdin>:1: ['*'[SSL: CERTIFICATE_VERIFY_FAILED]'*'] https://wrong.host.badssl.com/')
        echo ok 3;;
    '<stdin>:1: ['*'[CertificateError:'*']] https://wrong.host.badssl.com/')
        echo ok 3;;
    "<stdin>:1: [hostname 'wrong.host.badssl.com' doesn't match "*"] https://wrong.host.badssl.com/")
        echo ok 3;;
    *)
        echo not ok 3;;
esac
out=$("$prog" <<< 'http://[\S]+')
if [[ -z $out ]]
then
    echo ok 4
else
    sed -e 's/^/# /' <<< "$out"
    echo not ok 4
fi

# vim:ts=4 sts=4 sw=4 et ft=sh
