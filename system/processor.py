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

        self._port_id = 0x00  # type: hex
        self._in_port = 0x00  # type: hex
        self._out_port = 0x00  # type: hex

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
    def port_id(self) -> hex:
        return self._port_id

    def set_port_id(self, val: hex):
        self._port_id = val

    @property
    def in_port(self) -> hex:
        return self._in_port

    def set_int_port(self, val: hex):
        self._in_port = val

    @property
    def out_port(self) -> hex:
        return self._out_port

    def set_out_port(self, val: hex):
        self._out_port = val

    @property
    def memory(self) -> Memory:
        return self._mem

    def execute(self) -> None:
        self.fetch_program(self.manager.pc).exec(self)

    def add_instruction(self, instr):
        self._instructions.append(instr)

    def fetch_program(self, addr: hex):
        return self._instructions[addr]

    def outside_program(self) -> bool:
        return self.manager.pc == (len(self._instructions))
