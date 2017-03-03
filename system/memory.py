import itertools
import math
import random
from typing import Dict, List


class Memory(object):
    class MemoryRow(object):
        def __init__(self, width, default=None):
            self.width = width
            self.values = [default if default is not None
                           else bool(random.randint(0, 1)) for _ in range(0, self.width)]
            self.max_value = math.pow(2, self.width) - 1
            self.min_value = -math.pow(2, self.width - 1)

        @property
        def value(self) -> int:
            """returns the decimal value of the memory row"""
            return sum([int(v) * (1 << (len(self.values) - 1 - index))
                        for index, v in enumerate(self.values)])

        def set_value(self, value: int) -> None:
            """set the memory row value to a decimal value, converted to two's comp if negative"""
            if value > self.max_value:
                value = int(value % (self.max_value + 1))
            if value < self.min_value:
                value = int(value % (self.min_value - 1))
            # if negative, compute two's comp
            if value < 0:
                # skip over the -0b prefix with 3:
                binary = bin(abs(value) - (1 << self.width))[3:]
            else:
                # skip over the 0b prefix with 2:
                binary = bin(value)[2:]
            # 0 extend with itertools chain
            self.values = [bool(int(x)) for x in itertools.chain(
                [False for _ in range(0, len(self.values) - len(binary))], binary)]

    PROGRAM_WIDTH = 18  # type: int
    PROGRAM_LENGTH = 1024  # type: int
    DATA_WIDTH = 6  # type: int
    DATA_LENGTH = 64  # type: int
    REGISTER_WIDTH = 16  # type: int
    NUM_REGISTERS = 16  # type: int

    def __init__(self):
        self._REGISTERS = Memory.init_reg(Memory.REGISTER_WIDTH, Memory.NUM_REGISTERS)
        self._PROGRAM_MEMORY = Memory.init_mem(Memory.PROGRAM_WIDTH, Memory.PROGRAM_LENGTH)
        self._DATA_MEMORY = Memory.init_mem(Memory.DATA_WIDTH, Memory.DATA_LENGTH)

    @staticmethod
    def init_reg(width: int, num_reg: int) -> Dict[str, MemoryRow]:
        return {'s%0.1x' % x: Memory.MemoryRow(width, default=False) for x in range(0, num_reg)}

    @staticmethod
    def init_mem(width: int, length: int) -> List[MemoryRow]:
        return [Memory.MemoryRow(width) for _ in range(0, length)]

    def fetch_register(self, reg_name: str) -> int:
        return self._REGISTERS[reg_name.lower()].value

    def fetch_data(self, address: int) -> int:
        return self._DATA_MEMORY[address].value

    def fetch_program(self, address: int) -> int:
        return self._PROGRAM_MEMORY[address].value

    def fetch_data_reg(self, register: str) -> int:
        return self._DATA_MEMORY[self.fetch_register(register)].value

    def set_register(self, reg_name: str, value: int) -> None:
        if not isinstance(value, int):
            raise Exception("Value must be a number")
        self._REGISTERS[reg_name.lower()].set_value(value)

    def store_data(self, address: int, value: int) -> None:
        if not isinstance(value, int):
            raise Exception("Value must be a number")
        self._DATA_MEMORY[address].set_value(value)

    def store_data_reg(self, register: str, value: int) -> None:
        if not isinstance(value, int):
            raise Exception("Value must be a number")
        self._DATA_MEMORY[self.fetch_register(register)].set_value(value)
