"""
PicoSim - Xilinx PicoBlaze Assembly Simulator in Python
Copyright (C) 2017  Vadim Korolik - see LICENCE
"""
from system.memory import Memory
from system.manager import ProgramManager


class Processor(object):
    def __init__(self):
        self._mem = Memory()
        self.manager = ProgramManager()
        self._instructions = []
        self._carry = False  # type: bool
        self._zero = False  # type: bool

    @property
    def carry(self) -> bool:
        return self._carry

    def set_carry(self, val: bool):
        self._carry = val

    @property
    def zero(self) -> bool:
        return self._zero

    def set_zero(self, val: bool):
        self._zero = val

    @property
    def memory(self) -> Memory:
        return self._mem

    def execute(self) -> None:
        self.fetch_program(self.manager.pc).exec(self)

    def add_instruction(self, instr):
        self._instructions.append(instr)

    def fetch_program(self, addr: hex):
        return self._instructions[addr]

    def last(self) -> bool:
        return self.manager.pc == (len(self._instructions))
