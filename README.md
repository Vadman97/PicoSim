# PicoSim - Xilinx PicoBlaze Assembly Simulator
Copyright (C) 2017  Vadim Korolik - see [LICENCE] (https://github.com/Vadman97/PicoSim/blob/master/LICENSE)

[ISR] (https://www.xilinx.com/support/documentation/ip_documentation/ug129.pdf)

## Project Goals
The ultimate goal is to create a easy-to-use GUI simulator that will allow simple hookups for Verilog top level logic
to the soft-core CPU and complete simulation of assembly code, with realistic simulation of outputs to top-level LEDS
and SSDs as well as button/switch inputs.

Working on basic instruction simulation first. Once the assembler is complete and the assembly simulation is tested,
I will work on an interface for connecting top level logic to the CPU. After this functions, I plan to expand
this project into a web application to implement a GUI.

## TODO / Notes:
System IO (simulated portin/portout address-controlled multiplexing).
CPU Execution should be at a hard-set rate.
Debugging / execution should control instruction exec rate via ProgramManager.
Look into performance difference if we switch to numpy for the memory backend.
Memory operations are quite efficient, except set_value and get_value for a memory row taking more time during
conversion of binary to int. This process can definitely be optimized.

On an average machine, the ALU simulation is on the order of 500x slower than on FPGA (runs at 170 KHz).


