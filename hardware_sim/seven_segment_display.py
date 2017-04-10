from typing import Dict


class DisplaySegment(object):
    ON_STR_HORIZ = "==="
    OFF_STR_HORIZ = "___"
    ON_STR_VERT = "B"
    OFF_STR_VERT = "|"

    def __init__(self):
        self.anode = True  # type: bool
        self.cathodes = {chr(c): False for c in range(ord('a'), ord('f') + 1)}  # type: Dict[str: bool]
        self.cathodes["dp"] = False

    def __repr__(self):
        r = ".%s.\n%s...%s\n%s...%s\n.%s%s" % \
            (self.ON_STR_HORIZ if self.cathodes["a"] else self.OFF_STR_HORIZ,
             self.ON_STR_VERT if self.cathodes["f"] else self.OFF_STR_VERT,
             self.ON_STR_VERT if self.cathodes["b"] else self.OFF_STR_VERT,
             self.ON_STR_VERT if self.cathodes["e"] else self.OFF_STR_VERT,
             self.ON_STR_VERT if self.cathodes["c"] else self.OFF_STR_VERT,
             self.ON_STR_HORIZ if self.cathodes["a"] else self.OFF_STR_HORIZ,
             "*" if self.cathodes["dp"] else ".")
        return r


class SevenSegmentDisplay(object):
    def __init__(self):
        self.segments = [DisplaySegment() for _ in range(0, 8)]
