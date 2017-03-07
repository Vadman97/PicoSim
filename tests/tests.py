"""
PicoSim - Xilinx PicoBlaze Assembly Simulator in Python
Copyright (C) 2017  Vadim Korolik - see LICENCE
"""
import random
import time
import unittest

import ops.operations as op
from system.memory import Memory
from system.processor import Processor

MAX = 255
MIN = -128
ITERATIONS = 10000


def make_positive(a: int) -> int:
    s = a if a > -1 else -(abs(a) % abs(MIN - 1)) + (1 << 8)
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
        for _ in range(0, ITERATIONS):
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
        self.mem.set_register("s1", MIN + 1)
        self.assertEqual(self.mem.fetch_register('s1'), -MIN + 1)
        self.mem.set_register("s1", MIN)
        self.assertEqual(self.mem.fetch_register('s1'), -MIN)
        self.mem.set_register("s1", MIN - 1)
        self.assertEqual(self.mem.fetch_register('s1'), 0)


class OperationTests(unittest.TestCase):
    def setUp(self):
        self.proc = Processor()
        self.r = Memory.MemoryRow(Memory.REGISTER_WIDTH)

    def test_arithmetic_ops_stress(self):
        for o in op.ArithmeticOperation.OPS.values():
            for i in range(0, ITERATIONS):
                v1 = random.randint(0, MAX)
                v2 = random.randint(0, MAX)
                self.proc.memory.set_register('s1', v1)
                self.proc.memory.set_register('s2', v2)
                op.ArithmeticOperation(o, 's1', ['s2']).exec(self.proc)
                self.assertEqual(self.proc.memory.fetch_register('s1'), make_positive(o(v1, v2)))

    def test_arithmetic_ops_stress_const(self):
        for o in op.ArithmeticOperation.OPS.values():
            for i in range(0, ITERATIONS):
                v1 = random.randint(0, MAX)
                c1 = random.randint(0, MAX)
                self.proc.memory.set_register('s1', v1)
                op.ArithmeticOperation(o, 's1', [c1]).exec(self.proc)
                self.assertEqual(self.proc.memory.fetch_register('s1'), make_positive(o(v1, c1)))

    def test_arithmetic_ops_stress_sum(self):
        for o in op.ArithmeticOperation.OPS.values():
            s = random.randint(1, 100)
            self.proc.memory.set_register('s1', s)
            for i in range(0, ITERATIONS):
                v = random.randint(1, 10)
                op.ArithmeticOperation(o, 's1', [v]).exec(self.proc)
                s = make_positive(o(s, v))
                self.assertEqual(self.proc.memory.fetch_register('s1'), s)

    def test_bitwise_ops_stress(self):
        for o in op.BitwiseOperation.OPS.values():
            for i in range(0, ITERATIONS):
                v1 = random.randint(0, MAX)
                self.proc.memory.set_register('s1', v1)
                self.proc.set_carry(False)
                op.BitwiseOperation(o, 's1').exec(self.proc)
                r = Memory.MemoryRow(Memory.REGISTER_WIDTH)
                r.set_value(v1)
                r.values = o(r)[0]
                self.assertEqual(self.proc.memory.fetch_register('s1'), r.value)

    def test_bitwise_ops(self):
        self.r.set_value(32)
        self.r.values = op.BitwiseOperation.shift_right_zero(self.r)[0]
        self.assertEqual(self.r.value, 16)

        self.r.set_value(32)
        self.r.values = op.BitwiseOperation.shift_left_zero(self.r)[0]
        self.assertEqual(self.r.value, 64)

        for i in range(0, ITERATIONS):
            v1 = random.randint(0, MAX)
            c = ((v1 << 1) | ((v1 & 0x80) >> 7)) % (MAX + 1)
            self.r.set_value(v1)
            self.r.values = op.BitwiseOperation.rotate_left(self.r)[0]
            self.assertEqual(self.r.value, c)

            c = ((v1 >> 1) | ((v1 & 1) << 7))
            self.r.set_value(v1)
            self.r.values = op.BitwiseOperation.rotate_right(self.r)[0]
            self.assertEqual(self.r.value, c)

            c = ((v1 << 1) & 0xFE) % (MAX + 1)
            self.r.set_value(v1)
            self.r.values = op.BitwiseOperation.shift_left_zero(self.r)[0]
            self.assertEqual(self.r.value, c)

            c = ((v1 >> 1) & 0x7F) % (MAX + 1)
            self.r.set_value(v1)
            self.r.values = op.BitwiseOperation.shift_right_zero(self.r)[0]
            self.assertEqual(self.r.value, c)

            c = ((v1 << 1) & 0xFE | 1) % (MAX + 1)
            self.r.set_value(v1)
            self.r.values = op.BitwiseOperation.shift_left_one(self.r)[0]
            self.assertEqual(self.r.value, c)

            c = ((v1 >> 1) & 0x7F | (1 << 7)) % (MAX + 1)
            self.r.set_value(v1)
            self.r.values = op.BitwiseOperation.shift_right_one(self.r)[0]
            self.assertEqual(self.r.value, c)

            c = ((v1 << 1) & 0xFE | (v1 & 1)) % (MAX + 1)
            self.r.set_value(v1)
            self.r.values = op.BitwiseOperation.shift_left_x(self.r)[0]
            self.assertEqual(self.r.value, c)

            c = ((v1 >> 1) & 0x7F | (v1 & 0x80)) % (MAX + 1)
            self.r.set_value(v1)
            self.r.values = op.BitwiseOperation.shift_right_x(self.r)[0]
            self.assertEqual(self.r.value, c)

            for b in [True, False]:
                self.proc.set_carry(b)
                c = (((v1 << 1) & 0xFE) | self.proc.carry) % (MAX + 1)
                self.proc.memory.set_register('s1', v1)
                o = op.BitwiseOperation(op.BitwiseOperation.OPS["SLA"], 's1')
                o.exec(self.proc)
                self.assertEqual(self.proc.memory.fetch_register('s1'), c)

                self.proc.set_carry(b)
                c = (((v1 >> 1) & 0x7F) | (self.proc.carry << 7)) % (MAX + 1)
                self.proc.memory.set_register('s1', v1)
                o = op.BitwiseOperation(op.BitwiseOperation.OPS["SRA"], 's1')
                o.exec(self.proc)
                self.assertEqual(self.proc.memory.fetch_register('s1'), c)

    def test_call(self):
        o = op.FlowOperation(op.FlowOperation.OPS["CALL"], 0x297)
        o.exec(self.proc)
        self.assertEqual(self.proc.manager.pc, 0x297)

        o = op.FlowOperation(op.FlowOperation.OPS["CALL"], 0x0)
        o.exec(self.proc)
        self.assertEqual(self.proc.manager.pc, 0x0)

        o = op.FlowOperation(op.FlowOperation.OPS["CALL"], 0x3FF)
        o.exec(self.proc)
        self.assertEqual(self.proc.manager.pc, 0x3FF)

        o = op.FlowOperation(op.FlowOperation.OPS["CALL"], 0x400)
        o.exec(self.proc)
        self.assertEqual(self.proc.manager.pc, 0x0)


class ProcessorTests(unittest.TestCase):
    def setUp(self):
        self.proc = Processor()

    def test_performance(self):
        v1 = random.randint(0, MAX)
        v2 = random.randint(0, MAX)
        self.proc.memory.set_register('s1', v1)
        self.proc.memory.set_register('s2', v2)
        # undo the SRX comparison hack
        self.proc.add_instruction(op.BitwiseOperation(op.BitwiseOperation.OPS["SRX"], 's3'))
        for o in op.ArithmeticOperation.OPS.values():
            for i in range(0, 500 // len(op.ArithmeticOperation.OPS)):
                instr = op.ArithmeticOperation(o, 's1', ['s2'])
                self.proc.add_instruction(instr)

        for o in op.BitwiseOperation.OPS.values():
            for i in range(0, 500 // len(op.BitwiseOperation.OPS)):
                instr = op.BitwiseOperation(o, 's1')
                self.proc.add_instruction(instr)

        # repeat these ops while the 8th bit is not a 1
        self.proc.add_instruction(op.ArithmeticOperation(op.ArithmeticOperation.OPS["ADD"], 's3', [1]))
        # SRX comparison hack
        self.proc.add_instruction(op.BitwiseOperation(op.BitwiseOperation.OPS["SLX"], 's3'))
        self.proc.add_instruction(op.FlowOperation(op.FlowOperation.OPS["JUMP NC"], 0x0))

        start_time = time.time()
        executed = 0
        while not self.proc.last():
            self.proc.execute()
            executed += 1

        dur = time.time() - start_time
        ops_per_sec = executed / dur
        eff_khz = 2.0 / 1000.0 * ops_per_sec  # on PicoBlaze, one operation takes two clocks
        print("--- %8.3f seconds, %d ops     ---" % (dur, executed))
        print("--- %8.0f ops per sec ---" % ops_per_sec)
        print("--- %8.1f KHz clock   ---" % eff_khz)
        self.assertGreater(ops_per_sec, 10000)


if __name__ == '__main__':
    unittest.main()
