import random
import unittest
import operator

import ops.operations as op
from system.memory import Memory
from system.processor import Processor


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.mem = Memory()

    def test_fetch_register(self):
        self.assertEqual(self.mem.fetch_register('s0'), 0)

    def test_set_fetch_register(self):
        self.assertEqual(self.mem.fetch_register('s1'), 0)
        self.mem.set_register('s1', 62)
        self.assertEqual(self.mem.fetch_register('s1'), 62)
        self.mem.set_register('s1', 0)
        self.assertEqual(self.mem.fetch_register('s1'), 0)
        self.mem.set_register('s2', 65535)
        self.assertEqual(self.mem.fetch_register('s2'), 65535)
        self.mem.set_register('s3', 65535)
        self.assertEqual(self.mem.fetch_register('s3'), 65535)

    def test_set_fetch_register_stress(self):
        reg = 's%0.1x' % random.randint(0x0, 0xF)
        for _ in range(0, 10000):
            val = random.randint(0, 65535)
            self.mem.set_register(reg, val)
            self.assertEqual(self.mem.fetch_register(reg), val)
            val = random.randint(-32768, 32767)
            c_val = val if val > 0 else val + (1 << 16)
            c_val %= 65536
            self.mem.set_register(reg, c_val)
            # check properly converted to 2s comp
            self.assertEqual(self.mem.fetch_register(reg), c_val)

    def test_register_edge(self):
        with self.assertRaises(KeyError):
            self.mem.set_register("s10", 0)

        self.mem.set_register("s1", 65536)
        self.assertEqual(self.mem.fetch_register('s1'), 0)

        self.mem.set_register("s1", 65537)
        self.assertEqual(self.mem.fetch_register('s1'), 1)

        self.mem.set_register("s1", -1)
        self.assertEqual(self.mem.fetch_register('s1'), 65535)
        self.mem.set_register("s1", -32768)
        self.assertEqual(self.mem.fetch_register('s1'), 32768)


class OperationTests(unittest.TestCase):
    OPS = [
        operator.and_,
        operator.add,
        operator.or_
    ]

    def setUp(self):
        self.proc = Processor()

    def test_all_ops_stress(self):
        for o in OperationTests.OPS:
            v1 = 1000  # random.randint(0, 65535)
            v2 = 2345  # random.randint(0, 65535)
            self.proc.memory.set_register('s1', v1)
            self.proc.memory.set_register('s2', v2)
            op.ArithmeticOperation(o, 's1', ['s2']).exec(self.proc)
            self.assertEqual(self.proc.memory.fetch_register('s1'), o(v1, v2))

            v1 = random.randint(0, 65535)
            c1 = random.randint(0, 65535)
            self.proc.memory.set_register('s1', v1)
            op.ArithmeticOperation(o, 's1', [c1]).exec(self.proc)
            self.assertEqual(self.proc.memory.fetch_register('s1'), o(v1, c1))

            s = 50
            self.proc.memory.set_register('s1', s)
            for i in range(0, 10000):
                v = random.randint(1, 10)
                op.ArithmeticOperation(o, 's1', [v]).exec(self.proc)
                s = o(s, v)
                self.assertEqual(self.proc.memory.fetch_register('s1'), s % 65536)


if __name__ == '__main__':
    unittest.main()
