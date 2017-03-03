from system.memory import Memory


class ProgramManager(object):
    def __init__(self):
        self._pc = 0x0  # type: hex

    @property
    def pc(self) -> hex:
        return self._pc

    def next(self):
        self._pc += Memory.PROGRAM_WIDTH

    def jump(self, address: hex):
        self._pc = address % Memory.PROGRAM_LENGTH
