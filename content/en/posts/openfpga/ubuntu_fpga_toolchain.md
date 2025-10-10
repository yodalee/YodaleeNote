---
title: Installing Open Source FPGA Toolchain on Ubuntu
date: 2023-04-07
categories:
- FPGA
- hardware
- Setup Guide
tags:
- FPGA
- ubuntu
forkme: ubuntu-icestorm-toolchain
AITranslated: true
lang: en
---
The story goes like this: about a year and a half ago, I spent a few months playing around with the FPGA I got from COSCUP. At that time, I was developing on my desktop, which runs Archlinux. Recently, for some reasons, I took out this board again, but this time, I switched to my new laptop, which is installed with Windows WSL and Ubuntu 22.04, and discovered that among the tools I listed in the [article]({{< relref "openfpga_blink">}}), including yosys, nextpnr, prjtrellis, only yosys could be installed using apt on Ubuntu, while the others had to be compiled manually, unlike on Archlinux where someone has already set up AUR for you.

This article is a note on installing tools, hoping to help others who want to play with Lattice FPGA on Ubuntu. It primarily references [this article](https://projectf.io/posts/building-ice40-fpga-toolchain/), as well as some issues from the tools' Github.
<!--more-->

The set of tools to be installed includes:
* [yosys](https://github.com/YosysHQ/yosys)
* [icestorm](https://github.com/YosysHQ/icestorm)
* [prjtrellis](https://github.com/YosysHQ/prjtrellis)
* [nextpnr](https://github.com/YosysHQ/nextpnr)
* [systemc](https://github.com/accellera-official/systemc)
* [verilator](https://www.veripool.org/verilator/)

# Required packages

Install git and wget
```
apt install git wget
```

Required tools:
```shell
apt install -y build-essential clang tcl-dev libreadline-dev \
  pkg-config bison flex libftdi-dev cmake \
  python3-dev libboost-all-dev libeigen3-dev
```

Others are not necessarily required, only need to manually run yosys's `make test`, and if you really write Verilog, you'll need to install these.
```shell
apt install -y iverilog gtkwave gawk
```

# yosys

Yosys is the only open-source synthesis tool available. It can be installed with apt using the [official package](https://packages.ubuntu.com/search?keywords=yosys).
```shell
apt install yosys 
```

However, after testing, I found it was not compatible with other tools that needed to be compiled manually, encountering an error `ERROR: Expecting string value but got integer 1.`. Therefore, it is recommended to compile it yourself:
```shell
git clone https://github.com/YosysHQ/yosys yosys
cd yosys
make -j$(nproc)
make test  # optional (requires iVerilog)
make install
```

# icestorm

Icestorm is a toolset used to generate configuration data for Lattice iCE40 FPGAs. I found two official packages, fpga-icestorm and fpga-icestorm-chipdb, but I haven't tested them, so I can't guarantee they'll work:

```shell
apt install fpga-icestorm fpga-icestorm-chipdb
```

Install from source code:

```shell
git clone https://github.com/YosysHQ/icestorm.git icestorm
cd icestorm
make -j$(nproc)
make install
```

# prjtrellis

Prjtrellis is the database of the device, used to generate the final bitstream to be burned into the device. Without it, the next step, nextpnr, cannot be compiled.

```shell
git clone --recursive https://github.com/YosysHQ/prjtrellis
cd prjtrellis/libtrellis
cmake -DCMAKE_INSTALL_PREFIX=/usr/local .
make
```

# nextpnr

Nextpnr is an open-source FPGA placement tool supporting Lattice's iCE40 and ECP5 product lines. The commands here compile for ECP5, but you can switch to `-DARCH=ice40` to compile nextpnr for iCE40.

```shell
git clone --recursive https://github.com/YosysHQ/nextpnr nextpnr
cd nextpnr
cmake . -DARCH=ecp5 -DCMAKE_INSTALL_PREFIX=/usr/local
make -j$(nproc)
make install
```

# SystemC

SystemC is used to write hardware models. I installed it myself because the official Ubuntu does not include the FindPackage file for cmake, which is annoying when compiling SystemC with Cmake.

```shell
wget https://github.com/accellera-official/systemc/archive/refs/tags/2.3.4.tar.gz -O systemc.tar.gz
tar zxf systemc.tar.gz
cd systemc-2.3.4
cmake -DCMAKE_INSTALL_PREFIX=/usr/local -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_STANDARD=17
make -j${NPROC} install
```

# Verilator

Verilator is arguably the highest quality open-source verification tool. If you want to play with open-source hardware, it's unavoidable (unless you simply don’t verify, but I doubt you'd dare). The reason for not using the official Ubuntu package is that the official version is not new enough; at least verilator v5.006 can verify packed structs more conveniently.
```shell
wget https://github.com/verilator/verilator/archive/refs/tags/v5.006.tar.gz -O verilator.tar.gz
tar zxf verilator.tar.gz
cd verilator-5.006
autoconf
./configure --prefix=${THE_PREFIX}
make -j${NPROC}
make install
```

# Testing

Test with a simple [blink](https://github.com/YodaLee/icesugar-playground).

```verilog
module blink (output reg led,
              input clk);
  localparam CNT_RST = 25_000_000;
  reg [24:0] counter;
  always @(posedge clk) begin
    if (counter == 25'd0) begin
      led <= led + 1;
      counter <= CNT_RST;
    end
    else begin
      counter <= counter - 1;
    end
  end
endmodule
```

Lattice Place File (LPF) blink.lpf
```txt
LOCATE COMP "clk" SITE "P6";
IOBUF PORT "clk" IO_TYPE=LVCMOS33;
FREQUENCY PORT "clk" 25 MHZ;

LOCATE COMP "led" SITE "A12";
IOBUF PORT "led" IO_TYPE=LVCMOS25;
```

Use the tools we just installed to compile:

```shell
yosys -p "synth_ecp5 -json blink.json" blink.v
nextpnr-ecp5 --25k --package CABGA256 --speed 6 --json blink.json --textcfg blink_out.config --lpf blink.lpf
ecpack blink_out.config blink.bin
```

You can produce a .bin file ready to be burned.

# Put it all together

Having discussed so much seems pointless, so here's a Dockerfile instead~~Talk is cheap. Show me the Dockerfile~~:
[ubuntu-icestorm-toolchain](https://github.com/yodalee/ubuntu-icestorm-toolchain)

Download and build using docker, and you can start developing Lattice FPGA.