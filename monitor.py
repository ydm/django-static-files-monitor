#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import os
import os.path
import subprocess
import sys
import time


# TODO: REWORK?
def _collect(path):
    prefix = 'Static files monitor (pid={}):'.format(os.getpid())
    print >> sys.stderr, "{} Change detected to '{}'.".format(prefix, path)
    print >> sys.stderr, "{} Change detected to '{}'.".format(prefix, path)
    print >> sys.stderr, '%s Triggering `collectstatic`.'.format(prefix)
    subprocess.check_call(['./manage.py', 'collectstatic', '--noinput'])


# TODO: REWORK?
def _find_settings_module(root=None):
    if root is None:
        root = os.getcwd()

    for dn in [e for e in os.listdir(root) if os.path.isdir(os.path.join(root, e))]:
        dp = os.path.join(root, dn)

        for fn in [e for e in os.listdir(dp) if os.path.isfile(os.path.join(dp, e))]:
            if fn == 'settings.py':
                return '%s.settings' % dn


# TODO: use regexp validator? plugins? *_flymake.*?
def _is_ignored(f):
    f = os.path.split(f)[-1]
    return f.startswith('.')


def _list_files(root):
    files = set()

    for t in os.walk(root):
        if _is_ignored(t[0]):
            continue

        for fn in t[2]:
            fp = os.path.join(t[0], fn)
            if not _is_ignored(fp):
                files.add(fp)

    return files


def _modified(path, times):
    if not os.path.isfile(path):
        return path in times

    try:
        mtime = os.stat(path).st_mtime
    except OSError:
        return True

    if path not in times:
        times[path] = mtime
        return False

    ret = mtime != times[path]
    times[path] = mtime     # update
    return ret


class Monitor(object):
    _times = {}

    def __init__(self, dirs=None, interval=1.0):
        self._dirs = dirs
        self._interval = interval

    def start(self):
        prefix = 'Static files monitor (pid=%d):' % os.getpid()
        print >> sys.stderr, '%s Starting...' % (prefix)
        self._monitor()

    def track(self, path):
        self._dirs.add(path)

    def _monitor(self):

        def inner():
            for path in self._dirs:
                for fp in _list_files(path):
                    if _modified(fp, self._times):
                        _collect(fp)
                        print('\a')
                        return

        while 1:
            inner()
            time.sleep(self._interval)


def main():
    # add cwd to sys.path
    sys.path.append(os.getcwd())

    # TODO: arguments...
    m = _find_settings_module()
    if m is None:
        sys.exit('Cannot find DJANGO_SETTINGS_MODULE.')

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', m)
    from django.conf import settings

    monitor = Monitor(settings.STATICFILES_DIRS)
    monitor.start()


if __name__ == '__main__':
    main()
