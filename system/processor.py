"""
PicoSim - Xilinx PicoBlaze Assembly Simulator in Python
Copyright (C) 2017  Vadim Korolik - see LICENCE
"""
from system.manager import ProgramManager
from system.memory import Memory


class Processor(object):
    """
    ExternalInterface is public to the outside of the CPU
    Verilog simulation should only be able to access the Processor.external object
    """
    class ExternalInterface(object):
        def __init__(self, proc):
            self.p = proc

        @property
        def carry(self) -> bool:
            return self.p.p_carry

        @property
        def zero(self) -> bool:
            return self.p.p_zero

        def set_interrupt(self, val: bool):
            self.p._interrupt = val

        @property
        def interrupt_ack(self) -> bool:
            return self.p.p_interrupt_ack

        def set_int_port(self, val: hex):
            self.p._in_port = val

        @property
        def port_id(self) -> hex:
            return self.p.p_port_id

        @property
        def out_port(self) -> hex:
            return self.p.p_out_port

    def __init__(self, isr_addr=0x3FF):
        self._mem = Memory()
        self.manager = ProgramManager(isr_addr=isr_addr)
        self._last_instruction = 0
        self._instructions = {}  # type Dict[hex, Instruction]

        self.p_carry = False  # type: bool
        self.p_zero = False  # type: bool
        self.p_interrupt_ack = False  # type: bool
        self.p_out_port = 0x00  # type: hex
        self.p_port_id = 0x00  # type: hex

        self._interrupt_enabled = False  # type: bool
        self._interrupt = False  # type: bool

        self._preserved_carry = False  # type: bool
        self._preserved_zero = False  # type: bool

        self._in_port = 0x00  # type: hex

        self.external = Processor.ExternalInterface(self)

    """INTERNAL PUBLIC FUNCTIONS"""

    @property
    def interrupt_enabled(self) -> bool:
        return self._interrupt_enabled

    @property
    def interrupt(self) -> bool:
        return self._interrupt

    @property
    def in_port(self) -> hex:
        return self._in_port

    @property
    def memory(self) -> Memory:
        return self._mem

    def set_carry(self, val: bool):
        self.p_carry = val

    def set_zero(self, val: bool):
        self.p_zero = val

    def set_port_id(self, val: hex):
        self.p_port_id = val

    def set_out_port(self, val: hex):
        self.p_out_port = val

    def set_interrupt_enabled(self, val: bool):
        self._interrupt_enabled = val

    def set_interrupt_ack(self, val: bool):
        self.p_interrupt_ack = val

    def recover_zero(self):
        self.set_zero(self._preserved_zero)

    def recover_carry(self):
        self.set_carry(self._preserved_carry)

    def execute(self) -> None:
        if self.interrupt_enabled:
            if self.interrupt:
                self.memory.push_stack(self.manager.pc)
                self._preserved_zero = self.p_zero
                self._preserved_carry = self.p_carry
                self.set_interrupt_enabled(False)
                self.manager.jump(self.manager.isr_addr)
        self.fetch_program(self.manager.pc).exec(self)

    def set_instructions(self, instructions):
        self._instructions = instructions

    def add_instruction(self, instr):
        self._instructions[self._last_instruction] = instr
        self._last_instruction += 1

    def fetch_program(self, addr: hex):
        return self._instructions[addr]

    def outside_program(self) -> bool:
        return self.manager.pc == (len(self._instructions))
