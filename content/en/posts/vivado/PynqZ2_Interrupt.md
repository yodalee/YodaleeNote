---
title: 'Using Xilinx Development Board: Connecting Interrupt'
date: 2026-05-15
categories:
- FPGA
tags:
- Xilinx
- Vivado
series:
- XilinxBoard
AITranslated: true
---
The story goes like this. Generally speaking, in the workflow of IP, we use AXI Lite to write into the register to instruct the IP to start working. So, how do we know when the IP has completed its work?

The simplest method is to map the IP status to a register and have the driver continuously **harass** ~poll~ this register. This technique is called busy polling — it's simple and crude, but the downside is that the driver gets stuck here and can't do anything else.
Another method is that the IP issues an interrupt when it completes its task. Once the processor receives this interrupt, it signals the driver to handle the IP's post-processing tasks.

In this article, we'll look at how to accomplish this task.

# The IP for Experiment

The experimental IP works like this: it takes a 32-bit threshold as input, starts, and after computing for the threshold cycles, emits a done signal. 
As always, we use AI to help with the implementation:

> Implement an Interrupter module.  
> Input start and 32 bits threshold.  
> Output done and 32 bits id.  
> Upon start, run threshold cycles, assert and hold the done signal.  
> Increment id every time a done happens.  

Actually, the id is unnecessary; it can be removed.

# Connecting the Block Diagram

To package the IP, essentially refer to the previous [AXILite]({{<relref "PynqZ2_AXILite" >}}), connect two input registers 0, 1 to start and threshold; output registers 2, 3 to done, id.

The interrupt settings can be referenced from this [official interrupt article](https://pynq.readthedocs.io/en/v3.1/pynq_libraries/interrupt.html). The required module is AXI Interrupt Control, and the double-click settings are as follows:

* Our interrupt mode is level, set manually to 0xFFFFFFFFF
* Processor Interrupt Type is set to Level Interrupt
* Processor Interrupt Output connection is set to Single

Just like in the previous article, a complaint again: Xilinx, what's the issue with your UI? 
What is this auto/manual toggle about, and is Auto an edge interrupt or a level interrupt?

Double-click to open the configuration of the Zynq processor. In the Interrupt settings, enable the PL-PS Interrupt's F2P shared interrupt.

Start connecting, link the IP's done to Intr[0:0] in the Interrupt Control.
Connect the interrupt of the Interrupt Control to the IRQ_F2P port of the Zynq processor.
The finished block diagram is as follows:

# Test Results

Below is the python code used for testing, ol? will find the _interrupts object in the IP.

_content of _interrupts

## Test 1: Using Polling

Test results:

## Test 2: Using Interrupt

Since the interrupt uses Python's await to implement, it cannot be measured with timeit for a while, so I used time for a more direct test.

Test results show polling wins, with interrupts averaging 700 μs to inform the processor to proceed; whereas, with polling, the CPU reads the register update in an average of 60 μs once execution ends.

Not sure how much opening Fast Interrupt in the Interrupt Control will affect, will try it when possible.

# Conclusion

With this, we've covered the basics needed for playing with Xilinx boards. As long as we can assemble AXI Lite, AHB, AXI Stream, and Interrupt, connecting most IPs should not be a problem.