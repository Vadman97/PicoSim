from typing import List, Dict


class Line(object):
    def __init__(self, address: hex, instruction: str, tag: str):
        self.address = address
        self.tag = tag
        self.instruction = instruction


class Assembler(object):
    def __init__(self, path: str):
        self.path = path
        self.instructions = []  # type: List
        self.tag_address = {}  # type: Dict
        self.start_address = 0x0  # type: hex

    def parse(self):
        with open(self.path) as f:
            counter = 0
            for line in f.readlines():
                line = line.split(';')[0]
                line = line.split(':')
                tag = ""
                if len(line) > 1:
                    tag, line = line[0].strip(), "".join(line[1:])
                else:
                    line = line[0]
                line = line.strip()
                if not len(line):
                    continue

                # TODO parse constants too

                self.tag_address[tag] = self.start_address + counter
                self.instructions.append(Line(self.start_address + counter, line, tag))
                print(str(counter) + " " + tag + " " + line)
                counter += 1
