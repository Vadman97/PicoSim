from functools import reduce

from system.processor import Processor
from typing import List


class Instruction(object):
    def exec(self, proc: Processor):
        pass


class ArithmeticOperation(Instruction):
    def __init__(self, op, reg: str, args: List):
        self.operator = op
        self.register = reg
        self.args = [reg] + args

    def exec(self, proc: Processor):
        def expand(arg):
            if not isinstance(arg, int) and 's' in arg:
                return proc.memory.fetch_register(arg)
            else:
                return arg

        self.args = map(expand, self.args)  # load register values
        val = reduce(self.operator, self.args)  # apply operator
        proc.memory.set_register(self.register, val)  # set result
