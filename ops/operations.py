"""
PicoSim - Xilinx PicoBlaze Assembly Simulator in Python
Copyright (C) 2017  Vadim Korolik - see LICENCE
"""
import inspect
import operator
import sys
from functools import reduce
from typing import List, Dict, Callable, Tuple, Union

from system.memory import Memory
from system.processor import Processor


class Instruction(object):
    OPS = {}

    def exec(self, proc: Processor):
        pass

    def __repr__(self):
        return object.__repr__(self)


class AssemblerDirective(Instruction):
    OPS = {
        "ADDRESS": None,
        "CONSTANT": None
    }  # type: Dict[str, None]


class BitwiseOperation(Instruction):
    @staticmethod
    def rotate_left(register_row: Memory.MEMORY_IMPL) -> Tuple[List[bool], bool, int]:
        bits = register_row.values[1:8]
        bits.append(register_row.values[0])
        return bits, register_row.values[0], -1

    @staticmethod
    def rotate_right(register_row: Memory.MEMORY_IMPL) -> Tuple[List[bool], bool, int]:
        bits = [register_row.values[7]]
        bits += register_row.values[0:7]
        return bits, register_row.values[7], -1

    @staticmethod
    def shift_left_zero(register_row: Memory.MEMORY_IMPL) -> Tuple[List[bool], bool, int]:
        bits = register_row.values[1:8]
        bits.append(False)
        return bits, register_row.values[0], -1

    @staticmethod
    def shift_left_one(register_row: Memory.MEMORY_IMPL) -> Tuple[List[bool], bool, int]:
        bits = register_row.values[1:8]
        bits.append(True)
        return bits, register_row.values[0], 0

    @staticmethod
    def shift_left_x(register_row: Memory.MEMORY_IMPL) -> Tuple[List[bool], bool, int]:
        bits = register_row.values[1:8]
        bits.append(register_row.values[7])
        return bits, register_row.values[0], -1

    @staticmethod
    def shift_left_a(register_row: Memory.MEMORY_IMPL, carry: bool = False) -> Tuple[List[bool], bool, int]:
        bits = register_row.values[1:8]
        bits.append(bool(carry))
        return bits, register_row.values[0], 0

    @staticmethod
    def shift_right_zero(register_row: Memory.MEMORY_IMPL) -> Tuple[List[bool], bool, int]:
        bits = [False]
        bits += register_row.values[0:7]
        return bits, register_row.values[7], -1

    @staticmethod
    def shift_right_one(register_row: Memory.MEMORY_IMPL) -> Tuple[List[bool], bool, int]:
        bits = [True]
        bits += register_row.values[0:7]
        return bits, register_row.values[7], 0

    @staticmethod
    def shift_right_x(register_row: Memory.MEMORY_IMPL) -> Tuple[List[bool], bool, int]:
        bits = [register_row.values[0]]
        bits += register_row.values[0:7]
        return bits, register_row.values[7], -1

    @staticmethod
    def shift_right_a(register_row: Memory.MEMORY_IMPL, carry: bool = False) -> Tuple[List[bool], bool, int]:
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

    def __init__(self, op: Callable[[int, int], Tuple[List[bool], bool, int]], args: List[Union[str, int]]):
        self.operator = op
        self.register = args[0]
        self.proc = None  # type: Processor
        self.reg_row = None  # type: Memory.MEMORY_IMPL

    def exec(self, proc: Processor):
        self.proc = proc
        self.reg_row = self.proc.memory.REGISTERS[self.register.lower()]  # retrieve register memory row
        if self.operator is BitwiseOperation.shift_left_a or self.operator is BitwiseOperation.shift_right_a:
            bits, carry, zero = self.operator(self.reg_row, self.proc.external.carry)
        else:
            bits, carry, zero = self.operator(self.reg_row)
        # directly set result to memory
        self.proc.memory.REGISTERS[self.register.lower()].values = bits
        self.proc.set_carry(carry)
        if zero != -1:
            self.proc.set_zero(bool(zero))

        # increment pc
        self.proc.manager.next()

    def __repr__(self):
        return self.__class__.__name__ + " " + str(self.operator.__name__)


def addc(a: int, b: int) -> int:
    return operator.add(a, b)


def subc(a: int, b: int) -> int:
    return operator.sub(a, b)


class ArithmeticOperation(Instruction):

    OPS = {
        "ADD": operator.add,
        "ADDC": addc,
        "ADDCY": addc,
        "AND": operator.and_,
        "OR": operator.or_,
        "SUB": operator.sub,
        "SUBC": subc,
        "SUBCY": subc,
        "XOR": operator.xor
    }  # type: Dict[str, Callable[[int, int], int]]

    def expand(self, arg):
        if not isinstance(arg, int) and 's' in arg:
            return self.proc.memory.fetch_register(arg)
        else:
            return arg

    def __init__(self, op: Callable[[int, int], int], args: List[Union[str, int]]):
        self.operator = op
        self.register = args[0]
        self.o_args = args
        self.args = []  # type: List[int]
        self.proc = None  # type: Processor

    def exec(self, proc: Processor):
        self.proc = proc
        self.args = map(self.expand, self.o_args)  # load register values
        val = reduce(self.operator, self.args)  # apply operator
        if operator is addc or operator is subc:
            val += int(self.proc.external.carry)
        proc.memory.set_register(self.register, val)  # set result
        if operator is operator.and_ or operator is operator.or_ or operator is operator.xor:
            self.proc.set_carry(False)

        # increment pc
        self.proc.manager.next()


class CompareOperation(Instruction):
    @staticmethod
    def odd_parity(x: int) -> bool:
        parity = True
        while x:
            parity = not parity
            x &= (x - 1)

        return parity

    def comp(self, args):
        if args[0] == args[1]:
            self.proc.set_zero(True)
        elif args[0] < args[1]:
            self.proc.set_carry(True)

    def test(self, args):
        x = args[0] & args[1]
        if x:
            self.proc.set_zero(True)
        self.proc.set_carry(CompareOperation.odd_parity(x))

    OPS = {
        "COMP": comp,
        "COMPARE": comp,
        "TEST": test,
    }  # type: Dict[str, Callable[[List[Union[str, int]]], None]]

    def expand(self, arg):
        if not isinstance(arg, int) and 's' in arg:
            return self.proc.memory.fetch_register(arg)
        else:
            return arg

    def __init__(self, op: Callable[[List[Union[str, int]]], None], args: List[Union[str, int]]):
        self.operator = op
        self.register = args[0]
        self.o_args = args
        self.proc = None  # type: Processor

    def exec(self, proc: Processor):
        self.proc = proc
        args = list(map(self.expand, self.o_args))  # load register values
        self.operator(self, args)

        # increment pc
        self.proc.manager.next()


class DataOperation(Instruction):
    def fetch(self, args):
        self.proc.memory.set_register(args[0], self.proc.memory.fetch_data(args[1]))

    def store(self, args):
        self.proc.memory.store_data(args[1], self.proc.memory.fetch_register(args[0]))

    def input_(self, args):
        self.proc.set_port_id(args[1])
        self.proc.memory.set_register(args[0], self.proc.in_port)

    def output(self, args):
        self.proc.set_port_id(args[1])
        self.proc.set_out_port(self.proc.memory.fetch_register(args[0]))

    # TODO outputk
    def outputk(self, args):
        pass

    def load(self, args):
        self.proc.memory.set_register(args[0], args[1])

    OPS = {
        "FETCH": fetch,
        "STORE": store,
        "IN": input_,
        "INPUT": input_,
        "OUT": output,
        "OUTPUT": output,
        "OUTPUTK": outputk,
        "LOAD": load,
    }  # type: Dict[str, Callable[[List[Union[str, int]]], None]]

    def __init__(self, op: Callable[[List[Union[str, int]]], None], args: List[Union[str, int]]):
        self.operator = op
        self.register = args[0]
        self.second = args[1]
        self.proc = None  # type: Processor

    def exec(self, proc: Processor):
        self.proc = proc

        if not isinstance(self.second, int) and 's' in self.second:
            second = self.proc.memory.fetch_register(self.second)
        else:
            second = self.second

        self.operator(self, [self.register, second])

        # increment pc
        self.proc.manager.next()


class FlowOperation(Instruction):
    def call(self):
        self.proc.memory.push_stack(self.proc.manager.pc)
        self.jump()

    def call_c(self):
        self.call() if self.proc.external.carry is True else self.proc.manager.next()

    def call_nc(self):
        self.call() if self.proc.external.carry is False else self.proc.manager.next()

    def call_nz(self):
        self.call() if self.proc.external.zero is False else self.proc.manager.next()

    def call_z(self):
        self.call() if self.proc.external.zero is True else self.proc.manager.next()

    def jump(self):
        self.proc.manager.jump(self.address)

    def jump_c(self):
        self.jump() if self.proc.external.carry is True else self.proc.manager.next()

    def jump_nc(self):
        self.jump() if self.proc.external.carry is False else self.proc.manager.next()

    def jump_nz(self):
        self.jump() if self.proc.external.zero is False else self.proc.manager.next()

    def jump_z(self):
        self.jump() if self.proc.external.zero is True else self.proc.manager.next()

    # TODO JUMP@
    def jump_at(self):
        pass

    def return_(self):
        self.proc.manager.jump(self.proc.memory.pop_stack() + Memory.PROGRAM_WIDTH)

    def return_c(self):
        self.return_() if self.proc.external.carry is True else self.proc.manager.next()

    def return_nc(self):
        self.return_() if self.proc.external.carry is False else self.proc.manager.next()

    def return_nz(self):
        self.return_() if self.proc.external.zero is False else self.proc.manager.next()

    def return_z(self):
        self.return_() if self.proc.external.zero is True else self.proc.manager.next()

    def en_interrupt(self):
        self.proc.set_interrupt_enabled(True)
        self.proc.manager.next()

    def dis_interrupt(self):
        self.proc.set_interrupt_enabled(False)
        self.proc.manager.next()

    def return_i(self):
        self.proc.manager.jump(self.proc.memory.pop_stack())
        self.proc.recover_zero()
        self.proc.recover_carry()

    def return_i_disable(self):
        self.return_i()
        self.proc.set_interrupt_enabled(False)

    def return_i_enable(self):
        self.return_i()
        self.proc.set_interrupt_enabled(True)

    OPS = {
        "CALL": call,
        "CALL C": call_c,
        "CALL NC": call_nc,
        "CALL NZ": call_nz,
        "CALL Z": call_z,
        "RET": return_,
        "RET C": return_c,
        "RET NC": return_nc,
        "RET NZ": return_nz,
        "RET Z": return_z,
        "RETURN": return_,
        "RETURN C": return_c,
        "RETURN NC": return_nc,
        "RETURN NZ": return_nz,
        "RETURN Z": return_z,
        "JUMP": jump,
        "JUMP C": jump_c,
        "JUMP NC": jump_nc,
        "JUMP NZ": jump_nz,
        "JUMP Z": jump_z,
        "JUMP@": jump_at,
        "EINT": en_interrupt,
        "ENABLE INTERRUPT": en_interrupt,
        "DINT": dis_interrupt,
        "DISABLE INTERRUPT": dis_interrupt,
        "RETI DISABLE": return_i_disable,
        "RETURNI DISABLE": return_i_disable,
        "RETI ENABLE": return_i_enable,
        "RETURNI ENABLE": return_i_enable,

    }  # type: Dict[str, Callable[[], None]]

    def __init__(self, op: Callable[[], None], args: List[Union[hex, int]]):
        self.operator = op
        self.address = int(args[0]) if len(args) else None
        self.proc = None  # type: Processor

    def exec(self, proc: Processor):
        self.proc = proc
        self.operator(self)


OP_CLASSES = [obj for name, obj in inspect.getmembers(sys.modules[__name__],
                                                      lambda member: inspect.isclass(member)
                                                      and member.__module__ == __name__)]

ALL_OPS = {}

for x in OP_CLASSES:
    for op_name, op_func in x.OPS.items():
        ALL_OPS[op_name] = (x, op_func)
