#!/usr/bin/env python3

from __future__ import unicode_literals

import time
import unittest

from monitor import Future


class FutureTest(unittest.TestCase):

    def test_blocking(self):
        def worker(arg):
            time.sleep(2)
            return arg            

        begin = time.time()
        f = Future(worker, 2, 1000)
        actual = f()
        end = time.time()

        self.assertLessEqual(2, end - begin)
        return self.assertEqual(1000, f())

    def test_cancel(self):
        is_executed = False

        def worker():
            nonlocal is_executed
            is_executed = True
        
        f = Future(worker, 2)
        time.sleep(1)
        f.cancel()

        self.assertIsNone(f())
        self.assertFalse(is_executed)


if __name__ == '__main__':
    unittest.main()
