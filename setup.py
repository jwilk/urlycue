# encoding=UTF-8

# Copyright © 2016-2017 Jakub Wilk <jwilk@jwilk.net>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

'''
This setup script is only for pip.
Do not use directly.
'''

import distutils
import glob
import sys

if 'setuptools' not in sys.modules:
    raise RuntimeError(' '.join(__doc__.splitlines()))

int(*[], *[])  # Python >= 3.5 is required

def get_version():
    with open('doc/changelog', 'rt', encoding='UTF-8') as file:
        line = file.readline()
    return line.split()[1].strip('()')

distutils.core.setup(
    name='urlycue',
    version=get_version(),
    license='MIT License',
    description='command-line URL checker',
    url='http://jwilk.net/software/urlycue',
    author='Jakub Wilk',
    author_email='jwilk@jwilk.net',
    packages=['_urlycue.lib'],
    package_dir={'_urlycue': ''},
    data_files=[('share/man/man1', glob.glob('doc/*.1'))],
    entry_points=dict(
        console_scripts=['urlycue = _urlycue.lib.cli:main']
    ),
    install_requires=['aiohttp'],
)

# vim:ts=4 sts=4 sw=4 et
