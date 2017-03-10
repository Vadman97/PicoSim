"""
PicoSim - Xilinx PicoBlaze Assembly Simulator in Python
Copyright (C) 2017  Vadim Korolik - see LICENCE
"""
from typing import List, Dict

import ops.operations as op


class Line(object):
    def __init__(self, address: hex, instruction: str, tag: str):
        print("%d (tag %s): %s" % (address, tag, instruction))
        self.address = address
        self.tag = tag.lower()
        self.instruction = []
        # TODO: Does not work
        if ',' in instruction:
            self.instr_name = instruction.split(',')[0].upper()
        else:
            self.instr_name = instruction.split(' ')[0].upper()
        print(self.instr_name)
        self.instruction.append(self.instr_name)
        instruction = "".join(instruction.split(',')[1:])
        for x in instruction.lower().split(" "):
            x = x.strip()
            if x:
                self.instruction.append(x)
        # TODO: How to deal with
        # JUMP Z,      1FF
        # JUMP    200
        # JUMP@    (s2, s3)
        self.op = None  # type: op.Instruction

    def parse(self, constants: Dict[str, hex]):
        if self.instr_name == "ADDRESS":
            self.address = int(self.instruction[1], 16)
        else:
            for op_class in op.OP_CLASSES:
                if self.instr_name in op_class.OPS.keys():
                    op_type = op_class.OPS[self.instr_name]
                    args = self.instruction[1:]
                    for idx, each in enumerate(args):
                        if each in constants.keys():
                            args[idx] = constants[each]
                    print(args)
                    self.op = op_class(op_type, args)


class Assembler(object):
    def set_constant(self, l: Line):
        print(l.instruction)
        self.constants[l.instruction[1]] = int(l.instruction[2], 16)

    def __init__(self, path: str):
        self.path = path
        self.instructions = []  # type: List[Line]
        self.tag_address = {}  # type: Dict[str, hex]
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
                    tag, line = line[0].strip(), "".join(line[1:])
                else:
                    line = line[0]
                line = line.strip()
                if not len(line):
                    continue
                l = Line(self.start_address + counter, line, tag)
                if l.instr_name == "CONSTANT":
                    self.set_constant(l)
                else:
                    self.instructions.append(l)

                if len(tag):
                    self.tag_address[tag] = self.start_address + counter
                    tag = ""

                counter += 1

    def convert(self) -> Dict[int, op.Instruction]:
        operations = {}  # type: Dict[int, op.Instruction]
        for instr in self.instructions:
            instr.parse(self.constants)
            operations[instr.address] = instr.op
        return operations
