---
title: Digital Circuit Design Series - ScanChain and Their Origin
date: 2025-06-06
categories:
- ICdesign
tags:
- ICdesign
series:
- ICdesign
images:
- /images/ICdesign/scanchain.png
AITranslated: true
lang: en
---
In modern chip design, as chip functions become increasingly complex and the number of logic gates easily reaches billions, ensuring the chip can operate correctly post-manufacture has become a major challenging issue. Despite efforts from EDA software like Design Compiler and INNOVUS ensuring timing correctness in the design, process variations can also lead to chip defects. Therefore, we need an effective method to thoroughly test the chip’s internals before it hits the market. That's where Design for Testability (DFT) comes into play.

From EDA software descriptions, at least the following DFT techniques are supported:
* Boundary scan
* Scan Chain
* Core Wrapping
* Test points
* Compression

Each method has its unique know-how. In this article, we will focus on discussing Scan Chain. Its purpose is to connect originally invisible and untouchable registers into a data path that can be controlled and observed externally, allowing us to "scan" the internal state for logic testing.

# Scan Chain

Scan Chain is illustrated in the circuit diagram above, using the tool [digitaljs online](http://digitaljs.tilk.eu/). The chip's input and output will have three additional pins:
1. Scan Input
2. Scan Enable
3. Scan Output

All registers will be connected in a long series, and a mux will be added in front of the register to choose between:
1. Normal data input (D input): This is used for the original logical functionality input
2. Scan data input (Scan in): Used during testing to input test data externally

The scan chain connects from Scan Input through **every** register to Scan Output. This is a simple illustration with only two registers; a real scan chain could have tens of thousands of registers. Regarding input source selection, we use the control signal Scan Enable (or SE) to determine which mode the register should operate in:
* SE = 0: Function Mode. The register uses normal logical input
* SE = 1: Scan Mode. The register uses Scan input, operating like a shift register

In function mode, there's a Not gate between the two registers. How do we know this Not gate works well? With this structure, you can test the fabricated chip as follows:
1. Enable Scan Mode by turning on Scan Enable
2. Feed data from Scan Input, input a certain amount of clock to move the data to the corresponding position on the Scan Chain
3. Switch to Function Mode by turning off Scan Enable
4. Input a clock on the positive edge, storing the logical circuit output (output of the Not gate) into the output register
5. Enable Scan Mode by turning on Scan Enable again
6. Input a certain amount of clock to move data out from the Scan Chain and check if the Scan Output result is as expected

The combinational circuit, which might be deeply hidden in the circuit, becomes visible. After manufacturing, various test data can be fed into the chip to verify whether each transistor works well.

After understanding the Scan Chain, two questions remain:
1. How to insert the Scan Chain
2. How to generate test data for the Scan Chain

In this article, we’ll address the first question. In fact, I’m learning as I write, and the references used during this writing process are as follows:
* [Design Compiler for DFT](https://hackmd.io/@derek8955/SkoY2WNfh)
* [The difference between existing_dft and spec parameters in set_dft_signal -view](https://blog.csdn.net/SH_UANG/article/details/54767176)

If you have questions regarding the content or seek official documentation on the commands, look for the **DFT Compiler Manual**, not the Design Compiler Manual.

# Testing Module

To test how Design Compiler integrates Scan Chain, I implemented an ultra-simple module of about 100 lines
(yes, verilog with 100 lines is ultra-simple, and I assure it synthesizes within 10 seconds). Inside, it hits a register once, performs an addition, and then hits another register; normally, the first layer register isn’t needed in this implementation, but for testing DFT's effectiveness, please ignore my unrelated writing.

# Design Compiler Settings
The first part involves using Synopsys's DFT Compiler to insert a Scan Chain into verilog. DFT Compiler and Design Compiler are highly integrated, allowing the Scan Chain to be inserted during synthesis.

Referencing the tcl content tested practically, DFT has two insertion methods:
1. unmapped flow, starting from RTL
2. mapped flow, starting from the synthesized netlist

I’m unsure which is more common. The former can be written with a single tcl, completing it in one go; the latter can separate DFT’s tcl from the synthesis used tcl, first outputting the content into top_opt.ddc post-synthesis, then swapping to a DFT tcl to read it, insert the Scan Chain, and finally write out the verilog file.

## Preparing Test Protocol

We’ll view in sections. First, use create_port to add the scan_in, scan_en, scan_out ports in the output .syn.v since generally, people don’t want DFT code inserted into the original verilog code. After setting the scan clock and scan reset, call create_test_protocol to generate a test protocol, verifying that the DFT compiler understands your settings. The dft_drc outputs the following, later confirming there are no errors from dft_drc:

## Compile Scan
If you choose unmapped flow, you need to call the compile command now, adding the -scan parameter to turn your design from RTL to netlist, as preview_dft and insert_dft can only work on gate-level netlists. Adding the -scan parameter to compile will replace the existing D flip-flops (hereafter DFF) with testable Scan D flip-flops (hereafter SDFF).

An original DFF may have four pins: D input, Clock, Reset, and Q output; SDFF turns into six pins, adding scan’s ScanIn and ScanEn; before inserting DFT, ScanIn and ScanEn connect to 1'b0. Indeed, although you see the schematic describes adding a Mux in front of the DFF, SDFF has become so widely used that it directly makes an SDFF smaller in area than a separate Mux and DFF (still larger than a DFF, and comparing materials shows about 20% larger).

This is similar to multibit flip-flop (MBFF). Because circuit design frequently sees groups of registers updating their content under the same condition, a Multi-bit 2, 4, 6, or 8 standard cell is provided, allowing the design compiler to choose. Likewise, 2-1 signal inputs to flip-flops are so common that standard cells provide a Mux D flip-flop, reducing area.

## set_scan_configuration

After preparation, use set_scan_configuration; this command has several parameters. If your design isn’t vast, you can set it like here. It allows you to set things like scan chain length, count, and scan chain [type](https://blog.csdn.net/NBA_kobe_24/article/details/119952348). When using multiple clocks in large designs, -clock_mixing allows configuration on how scan signals cross clock domains.

But like with the previous Design Compiler section, if you’re handling such complex designs, you probably already have previous DFT settings and don’t need personal adjustment.

## Insert DFT
Use preview_dft to check what content the DFT compiler intends to insert. If all’s well, use insert_dft to insert the scan chain.

The result from preview_dft is as follows:

This points to another topic based on our settings:

Setting scan_en as ScanEnable signal, which is active high, changing 1 to 0 will make it active low. Of course, you *can* set it this way, but it causes significant issues. Since the prebuilt SDFF’s SI port is active high, setting an active low scan_en will lead to a bunch of inverters being inserted before your D flip-flops, unnecessarily increasing area. Don’t do this.

## Output Results
After adding DFT, you’ll need additional output files:

### Scan.sdc
Since scan testing doesn’t require the same conditions as chip operation, the [MMMC sample]({{< relref "APRmaterial#MMMC-檔">}}) shows both func and scan .sdc. Major differences lie mainly in Clock Timing; since it’s just for testing, high frequency isn’t necessary. Presently, because everything is housed in one .tcl, successful writing of a scan sdc file hasn’t occurred. Using the aforementioned mapped flow would separate the two types of .sdcs more readily.

### .spf
SPF stands for: Standard Test Interface Language (STIL) Procedure File (SPF). This file describes the chip’s interface, listing inputs, outputs, the existence of chains, how to enter Test Mode, etc. It can be generated by Design Compiler, or TetraMax, as hinted in documents, though that process hasn’t been experienced yet — future experiences will be shared when they occur.

### .scandef
The file name isn’t mandated; it’s descriptive, signifying a scan chain’s existence with respective settings for APR software.
During Place&Route, APR can reference scan chain settings with rearrangement capabilities, should P&R results require scan chain register order adjustments or register swaps between chains, more efficiently facilitating scan chain setup. For further details, see [introduction to scandef files and scan reorder](https://blog.csdn.net/weixin_44495082/article/details/136819364); explanations will follow as I experience them.

# Test Results
Below tabulate the synthesis outcomes for the tested module described above. As I composed this article, four distinct scenarios were examined:
1. No DFT configured, just plain synthesis (baseline)
2. DFT configured, synthesis with a -scan compilation followed by DFT insertion
3. No compile -scan use, a one-shot DFT configure and insert post compile
4. Same as 3, but recompilation with -inc after DFT insert

Area comparison:

| Setting | Area |
|:-|:-|
| No DFT | 1444 |
| compile -scan; insert_dft | 1729 |
| compile; insert_dft | 1759 |
| compile; insert_dft; compile -inc | 1658 |

The poorest outcome results when synthesis disregards DFT initially, inserting afterward. DFT compiler, during insertion, only executes limited optimization, leading to maximum area. If the -scan parameter’s added during synthesis, DFF relaxations to SDFF consideration allows slight area reductions through optimization.

Executing insert_dft prompts a degree of optimization from design compiler; since scan chains link registers thickly, they naturally provoke Min Delay Cost – fixable during APR if prohibited now.

The most area-efficient outcome follows DFT insertion with incremental compile. A trade-off occurs in additional compile timing; chronically, power leakage optimizations potentially introduces practicality, particularly for modern processes demanding such tasks.

# Conclusion
This article attempts an introduction on DFT ScanChain concept with personal limited knowledge. DFT is vast; discussed within is just a sliver of ScanChain intricacies. Multiple scan clock configurations exist, warranting consideration on clock domain crossings within multi-clock designs, STA execution post-CDC insertion, a realm of expertise only practical experiences fulfill.

Future audiences may cover generating vectors via TetraMax, DFT handling in INNOVUS APR, etc., retaining realistic opportunities for future sharing.

My conclusions echo [APR Preparations]({{< relref "APRmaterial">}}); if positioned therein, most document configurations would reflect previously substantiated practices. Learning from historic records prevails; detached responsibilities likely cite ineligibility toward ownership, safeguarding your monetary commitment from expenditure-driven action (or otherwise forbidden territory, eg lack of financial stake).

Nevertheless, **most tech firms are far removed from innovation**, embodying a prudent path ensuring consistent quarterly, annual advancements. From that stance, chip design parallels haven of familiarity, merely tweaking within framed fab contracts. Such may ring disenchanted, albeit not fostering somberness; over years, said approach fostered doubled smartphone performance, compounded battery life, and those 