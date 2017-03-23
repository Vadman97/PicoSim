"""
PicoSim - Xilinx PicoBlaze Assembly Simulator in Python
Copyright (C) 2017  Vadim Korolik - see LICENCE
"""
from system.memory import Memory


class ProgramManager(object):
    def __init__(self, isr_addr: hex = 0x3FF):
        self._pc = 0x0  # type: hex
        self.isr_addr = isr_addr

    @property
    def pc(self) -> hex:
        return self._pc

    def next(self):
        self._pc = (self._pc + 1) % Memory.PROGRAM_LENGTH

    def jump(self, address: hex):
        self._pc = address % Memory.PROGRAM_LENGTH
