---
title: Open FPGA Series - Block RAM
date: 2021-09-27
categories:
- FPGA
- verilog
tags:
- icesugar-pro
- verilog
series:
- FPGA
images:
- /images/openfpga/bram_image.jpg
forkme: icesugar-playground
AITranslated: true
lang: en
---
This update took a bit longer. The story goes like this: After testing HDMI, I spent some time trying to connect other devices with physical chips present on the FPGA board, including SDRAM, Flash, and SD card. The problem is that these aren't easy to connect, especially without an LA (Logic Analyzer), which makes it like a blind person feeling their way around. You can only use Verilator to simulate waveform; even if the waveform appears correct, if it doesn’t work when put into practice, you won't know what's wrong.

In general, these quirky components are often handled using dedicated tools like Altera/Quartus or Xilinx/Vivado. These tools include controllers IP from the FPGA manufacturer, allowing you to piece together a large module to manage these components with just a few mouse clicks. I remember when I was studying, my senior colleague didn't take this step. He manually created a DRAM controller, but later in the semester, everyone learned from a certain blog how to use the DRAM controller IP provided by Altera. Since then, no one (or needed to) made their exotic controllers.

For my use, I employed the Lattice tool, Lattice/Diamond, which allows usage with a free account, although I haven't activated it yet. Since it's an open FPGA, I'd like to avoid using proprietary tools as much as possible. The most likely open-source library I found is [litedram](https://github.com/enjoy-digital/litedram), which I plan to try if given the chance.

# BRAM

While I was fretting over the lack of SDRAM and Flash, my classmate Rui-Yang, known for sweeping through Boston as a formidable expert, suggested I first use the FPGA's built-in Block RAM. Unlike DRAM, it doesn’t involve a bunch of timing or charging issues. It’s as simple to use as logic and allows preset values to be stored during programming, which will be a great aid for my future projects. 
Yes, Icesugar-pro does include 1008 Kb of Block RAM; note that it's K bits, not K bytes, composed of 56 DP16KD 18 Kb components, which can be referenced in Lattice's document TN1264 ECP5 and ECP5-5G Memory Usage Guide.

As a verification project, I plan to stuff an image into the BRAM as a replacement for the last episode's vgatestsrc, displaying the image via HDMI. However, due to the 1008 Kb limit, we need to plan carefully on how to use it. The screen size is 640x480, which is 307200 pixels. DP16KD supports several modes: address/data width as 16384/1, 8192/2, 4096/4, 2048/9, 1024/18. I'm unsure why it's designed as the odd number of 18Kb, but anyway, the table below breaks it down:

| | |
|:-|:-|
| | num of DP16KD |
| data width 1 | 19 |
| data width 2 | 38 |
| data width 4 | ~~75~~ |
| data width 9 | ~~150~~ |
| data width 18 | ~~300~~ | 

Uh...basically, under the limit of 56 DP16KD, this is impossible unless a pixel is represented by 1 bit, which results in only two colors turning into [Bad Apple](https://youtu.be/FtutLA63Cp8), or 2 bits for only 4 grayscale colors like a Gameboy.

The solution is to reduce the screen size to 320x240, requiring only 76800 pixels:
| | |
|:-|:-|
| | num of DP16KD |
| data width 1 | 5 |
| data width 2 | 10 |
| data width 4 | 19 |
| data width 9 | 38 |
| data width 18 | ~~75~~ |

This way, at least 9 bits can represent colors, totaling 76800 pixels packed into 38 DP16KD components.

# BRAM module
The usage of BRAM can refer to this [tutorial note](https://zipcpu.com/tutorial/lsn-08-memory.pdf) I found. Basically, it's about following the guide; it's advisable to keep it in a separate file. The public interface includes clock, reset, write enable, and read enable, along with read/write addresses and values.
Use parameters to let users of this module configure different widths and depths of memory. Generally, the `SIZE` parameter might be `(1<<DEPTH)`, but not in this case. My DEPTH `$clog2(76800)` is 17 bits, but `1<<17=131072` would require 64 DP16KD, exceeding the usage limit, so we separate SIZE as another parameter.

Below, we use "ram" to declare memory blocks; initialize this space using readmemh/readmemb. For read/write sections, keeping it simple is best; writing too complicatedly can cause the synthesizer to misjudge the RAM as not memory, so avoid too many if conditions.

# source module
We present a module that determines what to display, receiving `newframe` and `enable` signals from the HDMI module, and then identifies the current position being displayed on the screen.

After creating a bram instance, the data to display are fetched from the bram. Since the screen size is still 640x480, we combine 4 pixels into one pixel, enlarging the 320x240 image stored in the bram into 640x480. The extracted data are restored to their original color by adding five 0s, although this color is bound to be distorted, which the results will show.

# Initialization
Image processing employs Python's PIL to adjust the size, take only the top three bits of each pixel's color, and compress colors into a 9-bit color space.

Pay attention that readmemh/readmemb operates such that if the memory data width is set to 9 bits, each line of data in your input file can only have 9 bits; any excess will automatically be ignored by readmemh/readmemb, which caused me a huge headache while debugging. Imagine the memory as a table with a width of 9 bits and a long length; your file corresponds line by line, and the file must have as many lines as the memory length, totaling 76800 lines in this case; it's similar for readmemh.

> JohnJohnLin: Please don't overestimate the intelligence of verilog tools

# Compilation
Declaring the bram allows you to browse the compilation message during compilation, finding the following sections:
We indeed used 38 DP16KD block memories. Additionally, the names appearing here are found in [ecp5 primitives](https://github.com/YosysHQ/nextpnr/blob/master/ecp5/docs/primitives.md), suggesting more intriguing components that haven't been used yet.

A large segment will also appear during the step of initializing our block ram:

Although, according to documentation, DP16KD is Dual Port, theoretically supporting two sets of distinct inputs for reading and writing, it's currently not doable using yosys, as it hits an unimplemented feature. Yosys won't match up synthesized Dual Port memories, which requires waiting for future updates or implementing it oneself.

# Execution
Replacing the original vgatestsrc with the above imagesrc, you can see the stored image displayed.
In a moment of uncertainty on what to display, I chose an image of the most handsome Huang Jin ~~~peko smile~~~ open-mouth smile of Nigo from the recent replay of Chinese Cuisine. The color is apparently blown out since we only have 512 colors. If we can get DRAM running, we might be able to go full-color, or even present slideshow features.

# Conclusion
In this chapter, we tackled BRAM, verifying that BRAM can achieve the following two desired functions:
- [X] Random access memory
- [X] Injecting initialized content externally for FPGA access
This equates to a significant first step, allowing us now to make great strides; next chapter should bring forth something very intriguing.