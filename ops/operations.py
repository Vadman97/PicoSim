"""
PicoSim - Xilinx PicoBlaze Assembly Simulator in Python
Copyright (C) 2017  Vadim Korolik - see LICENCE
"""
import operator
from functools import reduce
from typing import List, Dict, Callable, Tuple

from system.processor import Processor
from system.memory import Memory


class Instruction(object):
    def exec(self, proc: Processor):
        pass


class BitwiseOperation(Instruction):
    @staticmethod
    def rotate_left(register_row: Memory.MemoryRow) -> Tuple[List[bool], bool, int]:
        bits = register_row.values[1:8]
        bits.append(register_row.values[0])
        return bits, register_row.values[0], -1

    @staticmethod
    def rotate_right(register_row: Memory.MemoryRow) -> Tuple[List[bool], bool, int]:
        bits = [register_row.values[7]]
        bits += register_row.values[0:7]
        return bits, register_row.values[7], -1

    @staticmethod
    def shift_left_zero(register_row: Memory.MemoryRow) -> Tuple[List[bool], bool, int]:
        bits = register_row.values[1:8]
        bits.append(False)
        return bits, register_row.values[0], -1

    @staticmethod
    def shift_left_one(register_row: Memory.MemoryRow) -> Tuple[List[bool], bool, int]:
        bits = register_row.values[1:8]
        bits.append(True)
        return bits, register_row.values[0], 0

    @staticmethod
    def shift_left_x(register_row: Memory.MemoryRow) -> Tuple[List[bool], bool, int]:
        bits = register_row.values[1:8]
        bits.append(register_row.values[7])
        return bits, register_row.values[7], -1

    @staticmethod
    def shift_right_zero(register_row: Memory.MemoryRow) -> Tuple[List[bool], bool, int]:
        bits = [False]
        bits += register_row.values[0:7]
        return bits, register_row.values[7], -1

    @staticmethod
    def shift_right_one(register_row: Memory.MemoryRow) -> Tuple[List[bool], bool, int]:
        bits = [True]
        bits += register_row.values[0:7]
        return bits, register_row.values[7], 0

    @staticmethod
    def shift_right_x(register_row: Memory.MemoryRow) -> Tuple[List[bool], bool, int]:
        bits = [register_row.values[0]]
        bits += register_row.values[0:7]
        return bits, register_row.values[0], -1

    @staticmethod
    def shift_left_a(register_row: Memory.MemoryRow, carry: bool = False) -> Tuple[List[bool], bool, int]:
        bits = register_row.values[1:8]
        bits.append(bool(carry))
        return bits, register_row.values[0], 0

    @staticmethod
    def shift_right_a(register_row: Memory.MemoryRow, carry: bool = False) -> Tuple[List[bool], bool, int]:
        bits = [bool(carry)]
        bits += register_row.values[0:7]
        return bits, register_row.values[7], 0

    OPS = {
        "RL": rotate_left.__func__,
        "RR": rotate_right.__func__,
        "SL0": shift_left_zero.__func__,
        "SL1": shift_left_one.__func__,
        "SLX": shift_left_x.__func__,
        "SR0": shift_right_zero.__func__,
        "SR1": shift_right_one.__func__,
        "SRX": shift_right_x.__func__,
        "SLA": shift_left_a.__func__,
        "SRA": shift_right_a.__func__,
    }  # type: Dict[str, Callable[[int, int], Tuple[List[bool], bool, int]]]

    def __init__(self, op: Callable[[int, int], Tuple[List[bool], bool, int]], reg: str):
        self.operator = op
        self.register = reg
        self.proc = None  # type: Processor
        self.reg_row = None  # type: Memory.MemoryRow

    def exec(self, proc: Processor):
        self.proc = proc
        self.reg_row = self.proc.memory.REGISTERS[self.register.lower()]  # retrieve register memory row
        if self.operator is BitwiseOperation.shift_left_a or self.operator is BitwiseOperation.shift_right_a:
            bits, carry, zero = self.operator(self.reg_row, self.proc.carry)
        else:
            bits, carry, zero = self.operator(self.reg_row)
        # directly set result to memory
        self.proc.memory.REGISTERS[self.register.lower()].values = bits
        self.proc.set_carry(carry)
        if zero != -1:
            self.proc.set_zero(bool(zero))

        # increment pc
        self.proc.manager.next()


def addc(a: int, b: int) -> int:
    return operator.add(a, b)


def subc(a: int, b: int) -> int:
    return operator.sub(a, b)


class ArithmeticOperation(Instruction):
    OPS = {
        "ADD": operator.add,
        "ADDC": addc,
        "AND": operator.and_,
        "OR": operator.or_,
        "SUB": operator.sub,
        "SUBC": subc
    }  # type: Dict[str, Callable[[int, int], int]]

    def __init__(self, op: Callable[[int, int], int], reg: str, args: List):
        self.operator = op
        self.register = reg
        self.o_args = [reg] + args
        self.args = []  # type: List[int]
        self.proc = None  # type: Processor

    def exec(self, proc: Processor):
        def expand(arg):
            if not isinstance(arg, int) and 's' in arg:
                return proc.memory.fetch_register(arg)
            else:
                return arg

        self.proc = proc
        self.args = map(expand, self.o_args)  # load register values
        val = reduce(self.operator, self.args)  # apply operator
        if operator is addc or operator is subc:
            val += self.proc.carry
        proc.memory.set_register(self.register, val)  # set result
        if operator is operator.and_ or operator is operator.or_:
            self.proc.set_carry(False)

        # increment pc
        self.proc.manager.next()


class FlowOperation(Instruction):
    def call(self):
        self.proc.memory.push_stack(self.proc.manager.pc)
        self.jump()

    def call_c(self):
        if self.proc.carry is True:
            self.call()

    def call_nc(self):
        if self.proc.carry is False:
            self.call()

    def call_nz(self):
        if self.proc.zero is False:
            self.call()

    def call_z(self):
        if self.proc.zero is True:
            self.call()

    def jump(self):
        self.proc.manager.jump(self.address)

    def jump_c(self):
        if self.proc.carry is True:
            self.jump()

    def jump_nc(self):
        if self.proc.carry is False:
            self.jump()

    def jump_nz(self):
        if self.proc.zero is False:
            self.jump()

    def jump_z(self):
        if self.proc.zero is True:
            self.jump()

    def return_(self):
        self.proc.manager.jump(self.proc.memory.pop_stack() + Memory.PROGRAM_WIDTH)

    def return_c(self):
        if self.proc.carry is True:
            self.return_()

    def return_nc(self):
        if self.proc.carry is False:
            self.return_()

    def return_nz(self):
        if self.proc.zero is False:
            self.return_()

    def return_z(self):
        if self.proc.zero is True:
            self.return_()

    OPS = {
        "CALL": call,
        "CALL C": call_c,
        "CALL NC": call_nc,
        "CALL NZ": call_nz,
        "CALL Z": call_z,
        "JUMP": jump,
        "JUMP C": jump_c,
        "JUMP NC": jump_nc,
        "JUMP NZ": jump_nz,
        "JUMP Z": jump_z,
    }

    def __init__(self, op: Callable[[], None], address: hex):
        self.operator = op
        self.address = address
        self.proc = None  # type: Processor

    def exec(self, proc: Processor):
        self.proc = proc
        self.operator(self)
