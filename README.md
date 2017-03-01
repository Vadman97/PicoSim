# PicoSim - Xilinx PicoBlaze Assembly Simulator

[ISR] (https://www.xilinx.com/support/documentation/ip_documentation/ug129.pdf)

##TODO / Notes:
Ops: Operation parent class, indvidual ops that have some execute action
System: ProgramManager(Program Counter, state machine?), 
        MemoryMap(emulation of assembly memory manipulation), 
        IO (simulated portin/portout address-controlled multiplexing)

Debugging / execution should control instruction exec rate via ProgramManager
