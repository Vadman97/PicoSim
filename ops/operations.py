from system.memory import Memory


class AddLiteral(object):
    def __init__(self, register: str, literal: int):
        self.register = register
        self.literal = literal

    def exec(self, mem: Memory):
        mem.set_register(self.register, mem.fetch_register(self.register) + self.literal)


class AddRegister(object):
    def __init__(self, reg1: str, reg2: str):
        self.reg1 = reg1
        self.reg2 = reg2

    def exec(self, mem: Memory):
        mem.set_register(self.reg1, mem.fetch_register(self.reg1) + mem.fetch_register(self.reg2))
