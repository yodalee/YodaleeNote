---
title: Digital Circuit Design Series - Overview of the Tape-out Process
date: 2024-04-29
categories:
- ICdesign
tags:
- ICdesign
series:
- ICdesign
AITranslated: true
lang: en
---
Following up on our previous [introduction]({{< relref "introduction" >}}), today we will first look at an overview of the tape-out process. The goal of this article is to provide everyone with a basic understanding of the tape-out process, so that the subsequent articles will be easier to understand.
Originally, the plan was to quickly publish this article after finishing the introduction, but I decided to wait until the chip taped out in November returns and I confirm that the tape-out successfully meets the initial design before continuing with the subsequent articles. This way, I can speak with more confidence... Yes, it has to be that reason, and definitely not because I've been goofing off after work every day.

<!--more-->

The first thing to understand about chip design is the chip design that even Grandma can understand. It not only has an [online pdf](https://m105.nthu.edu.tw/~s105062901/ppt/RMaKnowsICDesignFlow.pdf) document but also a recorded YouTube video, which is very considerate. ~~With everything already explained, what else can I say?~~

{{< youtube kYUhk6FQwBc >}}

In this article, we will outline this process once again and also note some industry insights that I personally know. Everyone, feel free to take a look, and if there are any errors, please do not hesitate to correct me (though in my experience, no one will correct me):

In broad terms, I roughly divide the tape-out process into the following stages:
* HDL
* simulation
* synthesis
* post-synthesis simulation/LEC
* APR
* Post-layout simulation
* DRC/LVS verification

Each stage involves a great deal of software work. Indeed, given the complexity of digital circuits, every stage requires computer-aided design. Therefore, so-called hardware work is actually software work, and hardware engineers are also a kind of software engineer.
It is said that in the early days before EDA/CAD began to develop, the layout of the earliest Intel processors was hand-drawn, just like the rockets that landed on the moon back then. When you think about it, it's natural since there were no computers to run EDA.
However, times have changed now; without computers, you can't do anything. The major electronic design automation software is controlled by three companies: Synopsys, Cadence, and Siemens. These three will be constantly mentioned throughout the various processes below, and they are also the ones that many hardware companies in Taiwan pay software taxes to annually.

The detailed stages are described as follows:

# HDL
First, the design of the HDL starts from the required specification. Presently, the industry mainly uses two: VHDL and Verilog. Each camp has its regions of popularity and supporters. Generally, VHDL is used more in defense and aerospace, and it's popular in Europe.
Verilog is used more in the industry and is popular in the United States (and possibly Asia as well). As implementers, we don't have to think too much; we can just choose the one we are familiar with.

# Simulation
The most known simulation tools I know are Synopsys's VCS, Cadence's NCVerilog, and Xcelium. I tested and found that both VCS and Xcelium support SystemVerilog, so there is no reason not to use SystemVerilog with these tools.

It is worth mentioning that in the subsequent layout process, Cadence Innovus, in order to promote its own software, uses Xcelium to generate the toggle counter format (TCF) file format for power simulation. I haven't found a way for VCS to generate this setting, so if you're considering using Innovus for layout, you might want to keep this in mind.

I also tested two open-source tools: Icarus Verilog and Verilator. Icarus Verilog is simple to use, while Verilator is more complicated to install and use. However, the simulation speed of the two is not on the same level; Verilator is at least 10x to 100x faster than Icarus Verilog in simulation and also supports SystemVerilog.

Additionally, Icarus Verilog is an implementation for simulating Verilog. It can simulate actual time delays like Verilog's #1 #0.1, etc. On the other hand, Verilator analyzes the logic of registers and combinational circuits in Verilog, converting it into simulated C code. The generated simulation is based on Verilog's clock, and assigning a value to the clock will trigger the updated logic, but it cannot simulate actual time delays like #1.

# Synthesis

This step synthesizes the HDL we wrote into various logic gates used in actual circuits. This step is also done during FPGA verification of our design.

Let's talk about FPGA first. Currently, Xilinx and Altera dominate the market, with Xilinx taking the lion's share and Altera taking the leftover. They have been respectively acquired by AMD and Intel.

Using FPGAs requires exclusive software from each manufacturer; Xilinx has Vivado and Altera has Quartus. This kind of synthesis converts HDL into the look-up tables (LUTs) and flip-flops (FF) provided within the FPGA, as well as components like BRAM and DSP.

When making a chip, synthesis converts HDL into logic gates provided by the wafer fab. The tool I used for tape-out was Synopsys's Design Compiler, which is Synopsys's foundational product and likely the market's leading synthesis tool. Cadence also has the Genus Synthesis tool as a competitor.

# Post-synthesis simulation/LEC

After converting to logic gates, you can choose whether to proceed with post-synthesis simulation and logic equivalence check (LEC). At present, I didn't do LEC at this step and just relied on Verilog testing.

Since it has already been converted to logic gates, this step's simulation requires both the Verilog generated from synthesis and the standard delay format (.sdf) file. Simulating them together will yield correct results.

# APR

After synthesis is complete, you can prepare for layout. APR refers to Auto Place and Route, whose main tasks include:
* Placing the chip's pads for power, ground, signal lines, and other IO pads.
* Connecting power and ground from the chip's pads to the core of the chip.
* Placing logic gates in their actual positions.
* Connecting the logic gates' signal lines according to the synthesis results.
* Synthesizing the clock tree, so each logic gate receives the clock almost simultaneously as during simulation.

There is dedicated EDA software to complete these tasks nowadays. I used Cadence's Innovus for tape-out, while Synopsys has ICC2.

# Chip verification

After layout, the physical structure of the entire circuit is complete. To ensure the enormous cost of manufacturing the chip is not wasted, there are still many tasks that can be done, including but not limited to:

## Design Rule Check (DRC):
Check if the layout complies with the design rules defined by the wafer fab, such as whether the line width is too thin, too thick, or if two lines are too close.
As the process advances, design rules become increasingly complex. From basic processes to advanced ones, the number of rules may rise from hundreds to thousands, with various complicated and mixed rules, significantly increasing the check time. If you think your computer is fast, try running DRC, and you'll want to switch to the latest flagship CPU.
If the APR is done well, there shouldn't be major issues with DRC. Personally, I've encountered a single-digit number of track errors that couldn't be routed and finally resolved by manually editing the layout, but usually, this doesn't happen since digital ICs are composed of tens of thousands of transistors. It's impossible to manually solve hundreds or thousands of errors, so it's rare.

## Layout Versus Schematic (LVS):
Compare the layout and the schematic of the logic gates to see if they match. The underlying question is simple: build a diagram from the schematic and a separate diagram from the layout, and check if the two are isomorphic.

Like DRC above, from a digital IC perspective, APR tools have already laid out the design for you. Compared to my painstaking LVS checks when designing analog circuits, digital LVS checks are almost instantaneous, so there's no need to worry.

Can you skip this check? No, you can't. Even after APR, some minor edits might be necessary, such as moving component label text inside the chip or drawing some markings. If you accidentally connect lines, LVS will help check.

Regarding DRC and LVS, to the best of my knowledge, the leading brand is Siemens' Calibre, used for signoff for the final check. Others like Synopsys and Cadence have been pushing their DRC and LVS tools, but none have replaced Calibre as the final step.

## Parasitic EXtraction (PEX) and Gate-level simulation:
PEX involves using a tool after layout is complete to capture the parasitic resistances and capacitances among the components and wires, generating a spice file containing these parasitic elements.
This spice file is used with simulators for gate-level simulation. Generally, this step takes a lot of time; simulations that previously took hours might now take days. Personally, I have yet to perform gate-level simulation, so I will skip this part.

## Timing analysis:

After layout, the delays on all wires are finalized, generating another sdf file to confirm that the chip's timing meets requirements.
Synopsys's PrimeTime is the industry standard for this, but since I used Cadence INNOVUS for layout, which integrates Cadence's Tempus, and the chip worked without issue, I didn't use PrimeTime.

To borrow a quote from The Witch from Mercury:

> A chip not only relies on the process's performance, but also on the EDA and the designer's skills. Ultimately, the result itself is the only truth!

## Power Simulation:
After arranging the wires, you can also calculate the entire chip's power consumption based on simulation data, confirming that the voltage drop from the pad to the transistors isn't too severe.
I also used the power analysis integrated within INNOVUS with vcd or tcf files generated from simulation to conduct the power analysis. Synopsys's PrimePower is a competing tool, but I haven't used it, so I can't comment.

# PDK

All the tape-out steps mentioned above rely on the Process Design Kit (PDK) provided by the semiconductor manufacturer (foundry) responsible for the tape-out. The PDK includes necessary information for each step's software, such as:

* A list of logic gates provided by the standard cell library for synthesis.
* The electrical characteristics and SPICE models of transistors.
* Verilog files with delays for each logic gate, for use in post-synthesis simulation.

A specialized team in the fab usually maintains this, regularly down-sizing to measure its properties. Information for APR usage includes:

* GDSII layout of each component, allowing APR to directly place components in the layout.
* Definitions and electrical characteristics of each metal layer, and line width information.
* Definitions of each layer in the layout, including metal, text, and dummy layers.

Post-layout parts include:
* DRC/LVS/PEX rules. Alongside settings for software, documents provide detailed explanations and usually images for each rule in DRC.

Designers (us) feed these process documents into each EDA software to proceed with design. Without the PDK, there's no point in attempting tape-out, as you can't make a chip.

# Conclusion

Honestly, it's nearly impossible to fully grasp the nuances of producing an entire chip. In many companies, there may be a dedicated department for each step, or even outsourced to other fab companies. When you think about it, it's a miracle that digital circuits on the market actually work.
Our modern life depends on the sum of these miracles. Thanks to every IC design personnel who's worked diligently into the night, and thanks to every shift worker in the fabs.

In the next article, let's take a look at the physical structure of this little piece of human civilization's essence: the chip.