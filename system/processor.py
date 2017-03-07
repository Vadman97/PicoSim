from system.memory import Memory
from system.manager import ProgramManager


class Processor(object):
    def __init__(self):
        self._mem = Memory()
        self.manager = ProgramManager()
        self.instructions = []
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
        self.manager.next()

    def add_instruction(self, instr):
        self.instructions.append(instr)

    def fetch_program(self, addr: hex):
        return self.instructions[addr // Memory.PROGRAM_WIDTH]

    def done(self) -> bool:
        return (self.manager.pc / Memory.PROGRAM_WIDTH) == len(self.instructions)
