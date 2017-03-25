"""
PicoSim - Xilinx PicoBlaze Assembly Simulator in Python
Copyright (C) 2017  Vadim Korolik - see LICENCE
"""
import inspect
import operator
import sys
from functools import reduce
from typing import List, Dict, Callable, Union

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
    def rotate_left(self, register_row: Memory.MEMORY_IMPL) -> List[bool]:
        bits = register_row.values[1:8]
        bits.append(register_row.values[0])
        self.proc.set_carry(register_row.values[0])
        return bits

    def rotate_right(self, register_row: Memory.MEMORY_IMPL) -> List[bool]:
        bits = [register_row.values[7]]
        bits += register_row.values[0:7]
        self.proc.set_carry(register_row.values[7])
        return bits

    def shift_left_zero(self, register_row: Memory.MEMORY_IMPL) -> List[bool]:
        bits = register_row.values[1:8]
        bits.append(False)
        self.proc.set_carry(register_row.values[0])
        return bits

    def shift_left_one(self, register_row: Memory.MEMORY_IMPL) -> List[bool]:
        bits = register_row.values[1:8]
        bits.append(True)
        self.proc.set_carry(register_row.values[0])
        self.proc.set_zero(False)
        return bits

    def shift_left_x(self, register_row: Memory.MEMORY_IMPL) -> List[bool]:
        bits = register_row.values[1:8]
        bits.append(register_row.values[7])
        self.proc.set_carry(register_row.values[0])
        return bits

    def shift_left_a(self, register_row: Memory.MEMORY_IMPL, carry: bool = False) -> List[bool]:
        bits = register_row.values[1:8]
        bits.append(bool(carry))
        self.proc.set_carry(register_row.values[0])
        self.proc.set_zero(False)
        return bits

    def shift_right_zero(self, register_row: Memory.MEMORY_IMPL) -> List[bool]:
        bits = [False]
        bits += register_row.values[0:7]
        self.proc.set_carry(register_row.values[7])
        return bits

    def shift_right_one(self, register_row: Memory.MEMORY_IMPL) -> List[bool]:
        bits = [True]
        bits += register_row.values[0:7]
        self.proc.set_carry(register_row.values[7])
        self.proc.set_zero(False)
        return bits

    def shift_right_x(self, register_row: Memory.MEMORY_IMPL) -> List[bool]:
        bits = [register_row.values[0]]
        bits += register_row.values[0:7]
        self.proc.set_carry(register_row.values[7])
        return bits

    def shift_right_a(self, register_row: Memory.MEMORY_IMPL, carry: bool = False) -> List[bool]:
        bits = [bool(carry)]
        bits += register_row.values[0:7]
        self.proc.set_carry(register_row.values[7])
        self.proc.set_zero(False)
        return bits

    OPS = {
        "RL": rotate_left,
        "RR": rotate_right,
        "SL0": shift_left_zero,
        "SL1": shift_left_one,
        "SLX": shift_left_x,
        "SR0": shift_right_zero,
        "SR1": shift_right_one,
        "SRX": shift_right_x,
        "SLA": shift_left_a,
        "SRA": shift_right_a,
    }  # type: Dict[str, Callable[[Memory.MEMORY_IMPL], List[bool]]

    def __init__(self, op: Callable[[Memory.MEMORY_IMPL], List[bool]], args: List[Union[str, int]]):
        self.operator = op
        self.register = args[0]
        self.proc = None  # type: Processor
        self.reg_row = None  # type: Memory.MEMORY_IMPL

    def exec(self, proc: Processor):
        self.proc = proc
        self.reg_row = self.proc.memory.REGISTERS[self.register.lower()]  # retrieve register memory row
        if self.operator is BitwiseOperation.shift_left_a or self.operator is BitwiseOperation.shift_right_a:
            bits = self.operator(self, self.reg_row, self.proc.external.carry)
        else:
            bits = self.operator(self, self.reg_row)
        # directly set result to memory
        self.proc.memory.REGISTERS[self.register.lower()].values = bits

        # increment pc
        self.proc.manager.next()

    def __repr__(self):
        return self.__class__.__name__ + " " + str(self.operator.__name__)


class LogicOperation(Instruction):
    # operators will perform operations on the one bit of the memory row
    OPS = {
        "AND": operator.and_,
        "OR": operator.or_,
        "XOR": operator.xor
    }  # type: Dict[str, Callable[[bool, bool], bool]]

    def __init__(self, op: Callable[[bool, bool], bool], args: List[Union[str, int]]):
        self.operator = op
        self.register = args[0]
        if isinstance(args[1], str):
            self.argument = args[1]
            self.literal = False
        else:
            self.argument = Memory.MEMORY_IMPL(Memory.REGISTER_WIDTH, False)
            self.argument.set_value(args[1])
            self.literal = True

    def exec(self, processor: Processor):
        # retrieve the memory rows' binary directly without converting to decimal
        reg_row = processor.memory.REGISTERS[self.register].values
        if not self.literal:
            # look up the register binary
            bits = processor.memory.REGISTERS[self.argument].values
        else:
            # retrieve the converted literal as binary
            bits = self.argument.values

        zipped = zip(reg_row, bits)
        bits = list(map(lambda t: self.operator(t[0], t[1]), zipped))
        # set the memory row bits directly
        processor.memory.REGISTERS[self.register].values = bits

        # increment pc
        processor.manager.next()


def addc(a: int, b: int) -> int:
    return operator.add(a, b)


def subc(a: int, b: int) -> int:
    return operator.sub(a, b)


class ArithmeticOperation(Instruction):

    OPS = {
        "ADD": operator.add,
        "ADDC": addc,
        "ADDCY": addc,
        "SUB": operator.sub,
        "SUBC": subc,
        "SUBCY": subc,
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
        # TODO implement using carry lookahead
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
    def odd_parity(v: int) -> bool:
        parity = True
        while v:
            parity = not parity
            v &= (v - 1)

        return parity

    def comp(self, args):
        if args[0] == args[1]:
            self.proc.set_zero(True)
        elif args[0] < args[1]:
            self.proc.set_carry(True)

    def test(self, args):
        v = args[0] & args[1]
        if v:
            self.proc.set_zero(True)
        self.proc.set_carry(CompareOperation.odd_parity(v))

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
    # TODO change all the get/set instructions to directly set binary as opposed to converting back and forth
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

    def jump_at(self):
        upper = self.proc.memory.REGISTERS[self.address_parts[0]].values
        lower = self.proc.memory.REGISTERS[self.address_parts[1]].values
        # 12 bit JUMP@ instruction
        complete_row = Memory.MEMORY_IMPL(12, False)
        # lower 4 bits of upper segment
        complete_row.values = upper[3:7]
        # all of the lower segment
        complete_row.values.extend(lower)
        # jump to the address value
        self.address = complete_row.value
        self.jump()

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

    def __init__(self, op: Callable[[], None], args: List[Union[hex, int, str]]):
        self.operator = op
        if self.operator is FlowOperation.jump_at:
            self.address_parts = [args[0], args[1]]
        else:
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
