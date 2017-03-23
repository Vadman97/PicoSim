"""
PicoSim - Xilinx PicoBlaze Assembly Simulator in Python
Copyright (C) 2017  Vadim Korolik - see LICENCE
"""
from typing import List, Dict, Callable

import ops.operations as op


class ParseError(Exception):
    def __init__(self, message):
        self.message = message

    def __repr__(self):
        return "Error while parsing line - " + self.message

    def __str__(self):
        return str(self.__repr__())


class Line(object):
    NUMERIC_POSTFIXES = {
        "'b": 2,
        "'o": 8,
        "'d": 10,
        "'h": 16
    }

    def __init__(self, address: hex, instruction: str, tag: str):
        self.debug_string = "%d (tag %s): %s" % (address, tag, instruction)
        self.address = address
        self.tag = tag.lower()
        self.instruction_name = None  # type: str
        self.instruction_class = None
        self.instruction_operator = None  # type: Callable
        self.instruction_rest = []  # type: str
        self.instruction = None  # type: op.Instruction

        # to prevent JUMP    Z from being mesed up by spaces
        instruction = " ".join([x.strip() for x in instruction.split()])
        # remove parens from instruction
        instruction = instruction.translate(dict.fromkeys(map(ord, '()'), None))

        longest = 0
        for instr_name, instr_tuple in op.ALL_OPS.items():
            # make sure we found the longest instruction possible: jump z instead of jump
            if len(instr_name) > longest:
                if instr_name in instruction.upper():
                    if instruction.upper().index(instr_name) == 0:
                        self.instruction_name = instr_name
                        self.instruction_class = instr_tuple[0]
                        self.instruction_operator = instr_tuple[1]
                        self.instruction_rest = []
                        # strip whitespace and make sure we add stuff that's not blank
                        for x in instruction[len(self.instruction_name):].strip().lower().split(','):
                            x = x.strip()
                            # make sure its not blank, if its a numeric value convert to int
                            if len(x):
                                try:
                                    val = None
                                    found = False
                                    for postfix, base in Line.NUMERIC_POSTFIXES.items():
                                        if postfix in x:
                                            found = True
                                            # trim the 'b postfix
                                            val = int(x[:-2], base)
                                    if not found:
                                        # default hex
                                        val = int(x, 16)
                                except ValueError:
                                    val = x
                                self.instruction_rest.append(val)
                        # update the length of this instruction we found
                        longest = len(instr_name)
        if self.instruction_name is None:
            raise ParseError(self.debug_string)

    def __repr__(self):
        return self.debug_string if self.debug_string is not None else "Error: Unknown Line"

    def parse(self, constants: Dict[str, hex], tag_addresses: Dict[str, hex]):
        if self.instruction_name == "ADDRESS":
            self.address = int(self.instruction_rest[0], 16)
        else:
            for idx, each in enumerate(self.instruction_rest):
                for x in [constants, tag_addresses]:
                    if each in x.keys():
                        self.instruction_rest[idx] = x[each]
            self.instruction = self.instruction_class(self.instruction_operator, self.instruction_rest)


class Assembler(object):
    def set_constant(self, l: Line):
        self.constants[l.instruction_rest[0]] = l.instruction_rest[1]

    def __init__(self, path: str):
        self.path = path
        self.instructions = []  # type: List[Line]
        self.tag_addresses = {}  # type: Dict[str, hex]
        self.start_address = 0x0  # type: hex
        self.constants = {}  # type: Dict[str, hex]

    def parse(self):
        with open(self.path) as f:
            counter = 0
            tag = ""
            for line in f.readlines():
                line = line.split(';')[0]
                line = line.split(':')
                if len(line) > 1:
                    tag, line = line[0].strip().lower(), "".join(line[1:])
                else:
                    line = line[0]
                line = line.strip()
                if not len(line):
                    continue
                l = Line(self.start_address + counter, line, tag)
                if l.instruction_name == "CONSTANT":
                    self.set_constant(l)
                else:
                    self.instructions.append(l)

                # set tag constants (addresses)
                if len(tag):
                    self.tag_addresses[tag] = self.start_address + counter
                    tag = ""

                if l.instruction_name not in op.AssemblerDirective.OPS.keys():
                    counter += 1

    def convert(self) -> Dict[int, op.Instruction]:
        operations = {}  # type: Dict[int, op.Instruction]
        for instr in self.instructions:
            instr.parse(self.constants, self.tag_addresses)
            operations[instr.address] = instr.instruction
        return operations
