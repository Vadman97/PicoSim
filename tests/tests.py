import random
import unittest

import ops.operations as op
from system.memory import Memory


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
    def setUp(self):
        self.mem = Memory()

    def test_add_literal(self):
        self.mem.set_register('s1', 62)
        op.AddLiteral('s1', 8).exec(self.mem)
        self.assertEqual(self.mem.fetch_register('s1'), 70)

    def test_add_reg(self):
        self.mem.set_register('s1', 62)
        self.mem.set_register('s2', 843)
        op.AddRegister('s1', 's2').exec(self.mem)
        self.assertEqual(self.mem.fetch_register('s1'), 905)

    def test_add_literal_stress(self):
        s = 50
        self.mem.set_register('s1', s)
        for i in range(0, 32000):
            v = random.randint(1, 10)
            s += v
            op.AddLiteral('s1', v).exec(self.mem)
            self.assertEqual(self.mem.fetch_register('s1'), s % 65536)


if __name__ == '__main__':
    unittest.main()
