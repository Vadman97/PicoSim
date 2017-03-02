import random
import unittest

from system.memory import Memory


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.mem = Memory()

    def test_fetch_register(self):
        self.assertEqual(self.mem.fetch_register('s0').value, 0)

    def test_set_fetch_register(self):
        self.assertEqual(self.mem.fetch_register('s1').value, 0)
        self.mem.set_register('s1', 62)
        self.assertEqual(self.mem.fetch_register('s1').value, 62)
        self.mem.set_register('s1', 0)
        self.assertEqual(self.mem.fetch_register('s1').value, 0)
        self.mem.set_register('s2', 65535)
        self.assertEqual(self.mem.fetch_register('s2').value, 65535)
        self.mem.set_register('s3', 65535)
        self.assertEqual(self.mem.fetch_register('s3').value, 65535)

    def test_set_fetch_register_stress(self):
        reg = 's%0.1x' % random.randint(0x0, 0xF)
        for _ in range(0, 10000):
            val = random.randint(0, 65535)
            self.mem.set_register(reg, val)
            self.assertEqual(self.mem.fetch_register(reg).value, val)
            val = random.randint(-32768, 32767)
            cval = val if val > 0 else val + (1 << 16)
            self.mem.set_register(reg, val)
            # check properly converted to 2s comp
            self.assertEqual(self.mem.fetch_register(reg).value, cval)

    def test_register_edge(self):
        with self.assertRaises(KeyError):
            self.mem.set_register("s10", 0)
        with self.assertRaises(OverflowError):
            self.mem.set_register("s1", 65536)

        self.mem.set_register("s1", -1)
        self.assertEqual(self.mem.fetch_register('s1').value, 65535)
        self.mem.set_register("s1", -32768)
        self.assertEqual(self.mem.fetch_register('s1').value, 32768)


if __name__ == '__main__':
    unittest.main()
