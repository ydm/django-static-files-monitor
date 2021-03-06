#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright © 2013 Yordan Miladinov <yordan[at]4web.bg>
#
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

import importlib
import os
import os.path
import subprocess
import sys
import threading
import time

from six import print_


class Future(object):

    def __init__(self, func, wait=0, *args, **kwargs):
        self._cancel = threading.Event()
        self._wait = wait

        self._work  = threading.Lock()
        self._thread = threading.Thread(target=self._locked(func),
                                        args=args, kwargs=kwargs)
        self._result = None

        # Configurable autostart?
        self.start()

    def _locked(self, func):
        def wrapper(*args, **kwargs):
            self._work.acquire()
            try:
                if self._wait > 0:
                    self._cancel.wait(self._wait)

                cancel = self._cancel.is_set()

                # Now it's impossible to cancel the task
                self._cancel.set()

                if not cancel:
                    self._result = func(*args, **kwargs)
            finally:
                self._work.release()

        return wrapper

    def __call__(self):
        # Block until the lock is acquired
        self._work.acquire()
        try:
            return self._result
        finally:
            self._work.release()

    def start(self):
        return self._thread.start()

    def cancel(self):
        if self._cancel.is_set():
            return False
        self._cancel.set()
        return True


class Collector(object):

    def __init__(self):
        self._f = None

    def _do(self, path):
        prefix = 'Static files monitor (pid={}):'.format(os.getpid())
        print_("{} Change detected to '{}'.".format(prefix, path), file=sys.stderr)
        print_('{} Triggering `collectstatic`.'.format(prefix), file=sys.stderr)
        subprocess.check_call(['./manage.py', 'collectstatic', '--noinput'])
        print_('\a')           # a simple signal that the task is done

    def collect(self, path, wait=2):
        if self._f is not None:
            self._f.cancel()
        self._f = Future(self._do, wait, path)


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


class Monitor(object):

    def __init__(self, dirs=None, interval=1.0):
        self._dirs = dirs
        self._interval = interval

        self._collector = Collector()
        self._times = {}

    def start(self):
        prefix = 'Static files monitor (pid=%d):' % os.getpid()
        print_('{} Starting...'.format(prefix), file=sys.stderr)
        self._monitor()

    def track(self, path):
        self._dirs.add(path)

    def _modified(self, path):
        if not os.path.isfile(path):
            return path in self._times
    
        try:
            mtime = os.stat(path).st_mtime
        except OSError:
            return True
    
        if path not in self._times:
            self._times[path] = mtime
            return False
    
        ret = mtime != self._times[path]
        self._times[path] = mtime # update
        return ret

    def _monitor(self):

        def inner():
            for path in self._dirs:
                for fp in _list_files(path):
                    if self._modified(fp):
                        self._collector.collect(fp)
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

    settings = importlib.import_module(m)
    monitor = Monitor(settings.STATICFILES_DIRS)
    monitor.start()


if __name__ == '__main__':
    main()
