#!/usr/bin/env python3

import time
import unittest

import monitor


class FutureTest(unittest.TestCase):

    def test_blocking(self):
        def worker(arg):
            time.sleep(2)
            return arg            

        begin = time.time()
        f = monitor.Future(worker, 2, 0xdeadbeef)
        actual = f()
        end = time.time()

        self.assertLessEqual(2, end - begin)
        return self.assertEqual(0xdeadbeef, f())

    def test_cancel(self):
        is_executed = False

        def worker():
            nonlocal is_executed
            is_executed = True
            return 0xdeadbeef

        # The future task will wait 2 seconds before it starts
        f = monitor.Future(worker, 2)

        # Thus a second after the start the task should still be
        # cancel-able.
        time.sleep(1)

        # cancel() should return True when the cancellation is
        # successful
        self.assertTrue(f.cancel())

        self.assertFalse(f.cancel())

        # Assert f() doesn't block
        begin = time.time()
        self.assertIsNone(f())
        end = time.time()
        self.assertLess(end - begin, 0.1)

        # Assert the task function isn't executed
        self.assertFalse(is_executed)

    def test_cancel2(self):
        is_executed = False

        def worker():
            nonlocal is_executed
            time.sleep(2)
            is_executed = True
            return 0xdeadbeef

        # The future task will wait for a second before it starts the
        # worker
        f = monitor.Future(worker, 1)

        # The worker takes at least 2 seconds to execute.  Thus
        # currently it's being executed and a cancellation is
        # impossible.
        time.sleep(2)
        self.assertFalse(f.cancel())

        # Since there is roughly a second left for the future task to
        # complete, assert that time is greater than 0.9s
        begin = time.time()
        self.assertEqual(0xdeadbeef, f())
        end = time.time()
        self.assertLessEqual(0.9, end - begin)

        # Assert the task function was executed
        self.assertTrue(is_executed)


if __name__ == '__main__':
    unittest.main()
