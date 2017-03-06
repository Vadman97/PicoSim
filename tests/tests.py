import random
import unittest

import ops.operations as op
from system.memory import Memory
from system.processor import Processor

MAX = 255
MIN = -128


def make_positive(a: int) -> int:
    s = a if a > 0 else a + (1 << 8)
    return s % (MAX + 1)


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
        self.mem.set_register('s2', MAX)
        self.assertEqual(self.mem.fetch_register('s2'), MAX)
        self.mem.set_register('s3', MAX)
        self.assertEqual(self.mem.fetch_register('s3'), MAX)

    def test_set_fetch_register_stress(self):
        reg = 's%0.1x' % random.randint(0x0, 0xF)
        for _ in range(0, 10000):
            val = random.randint(0, MAX)
            self.mem.set_register(reg, val)
            self.assertEqual(self.mem.fetch_register(reg), val)
            val = random.randint(-32768, 32767)
            c_val = make_positive(val)
            self.mem.set_register(reg, c_val)
            # check properly converted to 2s comp
            self.assertEqual(self.mem.fetch_register(reg), c_val)

    def test_register_edge(self):
        with self.assertRaises(KeyError):
            self.mem.set_register("s10", 0)

        self.mem.set_register("s1", MAX + 1)
        self.assertEqual(self.mem.fetch_register('s1'), 0)

        self.mem.set_register("s1", MAX + 2)
        self.assertEqual(self.mem.fetch_register('s1'), 1)

        self.mem.set_register("s1", -1)
        self.assertEqual(self.mem.fetch_register('s1'), MAX)
        self.mem.set_register("s1", MIN)
        self.assertEqual(self.mem.fetch_register('s1'), -MIN)


class OperationTests(unittest.TestCase):
    def setUp(self):
        self.proc = Processor()
        self.v1 = random.randint(0, MAX)
        self.r = Memory.MemoryRow(Memory.REGISTER_WIDTH)

    def test_arithmetic_ops_stress(self):
        for o in op.ArithmeticOperation.OPS.values():
            v1 = random.randint(0, MAX)
            v2 = random.randint(0, MAX)
            self.proc.memory.set_register('s1', v1)
            self.proc.memory.set_register('s2', v2)
            op.ArithmeticOperation(o, 's1', ['s2']).exec(self.proc)
            self.assertEqual(self.proc.memory.fetch_register('s1'), make_positive(o(v1, v2)))

            v1 = random.randint(0, MAX)
            c1 = random.randint(0, MAX)
            self.proc.memory.set_register('s1', v1)
            op.ArithmeticOperation(o, 's1', [c1]).exec(self.proc)
            self.assertEqual(self.proc.memory.fetch_register('s1'), make_positive(o(v1, c1)))

            s = random.randint(1, 100)
            self.proc.memory.set_register('s1', s)
            for i in range(0, 10000):
                v = random.randint(1, 10)
                op.ArithmeticOperation(o, 's1', [v]).exec(self.proc)
                s = make_positive(o(s, v))
                self.assertEqual(self.proc.memory.fetch_register('s1'), s)

    def test_bitwise_ops_stress(self):
        for o in op.BitwiseOperation.OPS.values():
            for i in range(0, 10000):
                v1 = random.randint(0, MAX)
                self.proc.memory.set_register('s1', v1)
                op.BitwiseOperation(o, 's1').exec(self.proc)
                r = Memory.MemoryRow(Memory.REGISTER_WIDTH)
                r.set_value(v1)
                r.values = o(r)[0]
                self.assertEqual(self.proc.memory.fetch_register('s1'), r.value)

    # TODO(Vadim): Test against validated bitwise operators for the rest
    def test_bitwise_ops(self):
        c = ((self.v1 << 1) | (self.v1 >> (-1 & (8 * 8 - 1)))) % MAX
        self.r.set_value(self.v1)
        self.r.values = op.BitwiseOperation.rotate_left(self.r)[0]
        self.assertEqual(self.r.value, c)

        c = ((self.v1 >> 1) | ((self.v1 & 1) << 7))
        self.r.set_value(self.v1)
        self.r.values = op.BitwiseOperation.rotate_right(self.r)[0]
        self.assertEqual(self.r.value, c)


if __name__ == '__main__':
    unittest.main()
