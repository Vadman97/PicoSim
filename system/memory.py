"""
PicoSim - Xilinx PicoBlaze Assembly Simulator in Python
Copyright (C) 2017  Vadim Korolik - see LICENCE
"""
import itertools
import math
import random
from typing import Dict, List

import numpy as np


class Memory(object):
    class MemoryRow(object):
        def __init__(self, width: int, default: bool = False) -> None:
            self.width = width
            self.max_value = math.pow(2, self.width) - 1
            self.min_value = -math.pow(2, self.width - 1)
            self.default = default

        """If its too big and negative and too small, wrap"""
        def bounds(self, value: int) -> int:
            if value > self.max_value:
                value = int(value % (self.max_value + 1))
            if value < self.min_value:
                value = int(value % (self.min_value - 1))
            return value

        """Convert int to binary accounting for 2s comp for negatives"""
        def binary(self, value: int) -> str:
            # if negative, compute two's comp
            if value < 0:
                # skip over the -0b prefix with 3:
                binary = bin(abs(value) - (1 << self.width))[3:]
            else:
                # skip over the 0b prefix with 2:
                binary = bin(value)[2:]
            return binary

    class NumpyRow(MemoryRow):
        def __init__(self, width: int, default: bool = False) -> None:
            super(Memory.NumpyRow, self).__init__(width, default)
            self.values = np.array(np.zeros(self.width, np.uint8))
            self.binary_multiplier = np.array([1 << (self.width - 1 - idx) for idx, _ in enumerate(range(self.width))])

        @property
        def value(self) -> int:
            return int(np.sum(self.values * self.binary_multiplier))

        def set_value(self, value: int) -> None:
            value = self.bounds(value)
            # automatically performs 2s comp if needed
            binary = np.binary_repr(value, width=8)
            self.values = np.array(list(binary), dtype=np.uint8)

    class ArrayRow(MemoryRow):
        def __init__(self, width: int, default: bool = False) -> None:
            super(Memory.ArrayRow, self).__init__(width, default)
            self.values = [self.default if self.default is not None
                           else bool(random.randint(0, 1)) for _ in range(0, self.width)]

        @property
        def value(self) -> int:
            """returns the decimal value of the memory row"""
            return sum([int(v) * (1 << (len(self.values) - 1 - index))
                        for index, v in enumerate(self.values)])

        def set_value(self, value: int) -> None:
            """set the memory row value to a decimal value, converted to two's comp if negative"""
            value = self.bounds(value)
            binary = self.binary(value)
            # 0 extend with itertools chain
            self.values = [bool(int(x)) for x in itertools.chain(
                [False for _ in range(0, len(self.values) - len(binary))], binary)]

    PROGRAM_WIDTH = 18  # type: int
    PROGRAM_LENGTH = 1024  # type: int
    DATA_WIDTH = 8  # type: int
    DATA_LENGTH = 64  # type: int
    REGISTER_WIDTH = 8  # type: int
    NUM_REGISTERS = 16  # type: int
    STACK_WIDTH = 10  # type: int
    STACK_LENGTH = 31  # type: int

    MEMORY_IMPL = ArrayRow

    def __init__(self):
        self.REGISTERS = Memory.init_reg(Memory.REGISTER_WIDTH, Memory.NUM_REGISTERS)
        self.DATA_MEMORY = Memory.init_mem(Memory.DATA_WIDTH, Memory.DATA_LENGTH)
        self.STACK = Memory.init_mem(Memory.STACK_WIDTH, Memory.STACK_LENGTH)

        self.stack_pointer = 0  # type: int

    @staticmethod
    def init_reg(width: int, num_reg: int) -> Dict[str, MEMORY_IMPL]:
        return {'s%0.1x' % x: Memory.MEMORY_IMPL(width, default=False) for x in range(0, num_reg)}

    @staticmethod
    def init_mem(width: int, length: int) -> List[MEMORY_IMPL]:
        return [Memory.MEMORY_IMPL(width) for _ in range(0, length)]

    def fetch_register(self, reg_name: str) -> int:
        return self.REGISTERS[reg_name.lower()].value

    def fetch_data(self, address: int) -> int:
        return self.DATA_MEMORY[address].value

    def set_register(self, reg_name: str, value: int) -> None:
        if not isinstance(value, int):
            raise Exception("Value must be a number")
        self.REGISTERS[reg_name.lower()].set_value(value)

    def store_data(self, address: int, value: int) -> None:
        if not isinstance(value, int):
            raise Exception("Value must be a number")
        self.DATA_MEMORY[address].set_value(value)

    def push_stack(self, value: int) -> None:
        if self.stack_pointer > self.STACK_LENGTH - 1:
            raise IndexError("Stack overflow")
        self.STACK[self.stack_pointer].set_value(value)
        self.stack_pointer += 1

    def pop_stack(self) -> int:
        if self.stack_pointer <= 0:
            raise IndexError("Stack underflow")
        self.stack_pointer -= 1
        return self.STACK[self.stack_pointer].value
