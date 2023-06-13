---
title: "在 Ubuntu 上安裝開源 FPGA 工具鏈"
date: 2023-04-07
categories:
- FPGA
- hardware
- simple setup
tags:
- FPGA
- ubuntu
forkme: ubuntu-icestorm-toolchain
---

故事是這個樣子的，大概在一年半前，我花了幾個月小玩了一下從 COSCUP 那邊拿到的 FPGA，那時候是在我的桌電 - 也就是 Archlinux 上進行開發。  
最近因為一些原因又把這塊板子拿出來，但這次，我改用我新的筆電，裝的是 Windows 的 WSL 搭配 ubuntu 22.04，然後就發現，
我在[文章中]({{< relref "openfpga_blink">}})列出來的幾項工具，包括 yosys, nextpnr, prjtrellis，
只有 yosys 能在 ubuntu 上用 apt 完成安裝，其他都在自己編譯，不像 Archlinux 上有人幫你弄好 AUR 了。

這篇文就是安裝工具的筆記，希望能幫到其他想在 ubuntu 上玩 lattice FPGA 的人，
主要參考[這篇文章](https://projectf.io/posts/building-ice40-fpga-toolchain/)，以及一些工具 Github 的 issue。
<!--more-->

這一串會安裝的工具組包括：
* [yosys](https://github.com/YosysHQ/yosys)
* [icestorm](https://github.com/YosysHQ/icestorm)
* [prjtrellis](https://github.com/YosysHQ/prjtrellis)
* [nextpnr](https://github.com/YosysHQ/nextpnr)
* [systemc](https://github.com/accellera-official/systemc)
* [verilator](https://www.veripool.org/verilator/)

# 需要的 package

安裝 git 跟 wget
```
apt install git wget
```

需要的工具組：
```shell
apt install -y build-essential clang tcl-dev libreadline-dev \
  pkg-config bison flex libftdi-dev cmake \
  python3-dev libboost-all-dev libeigen3-dev
```

其他不是一定必要的，只有自己手動跑 yosys 的 `make test` ，以及真的寫 verilog 的話會需要裝的。
```shell
apt install -y iverilog gtkwave gawk
```

# yosys

yosys 是開源的合成工具，目前僅此一家別無分店。  
可以用 apt 安裝 [官方的 package](https://packages.ubuntu.com/search?keywords=yosys)。
```shell
apt install yosys 
```

但我測過之後，發現無法和其他要自己編譯的工具相容，遇到錯誤 `ERROR: Expecting string value but got integer 1.`。  
因此還是建議自行編譯：
```shell
git clone https://github.com/YosysHQ/yosys yosys
cd yosys
make -j$(nproc)
make test  # optional (requires iVerilog)
make install
```

# icestorm

icestorm 是用來生成 Lattice iCE40 FPGAs 設定資料的工具組，
有查到 fpga-icestorm 跟 fpga-icestorm-chipdb 兩個官方的 package，但我沒測過不保證能用：

```shell
apt install fpga-icestorm fpga-icestorm-chipdb
```

從 source code 安裝：

```shell
git clone https://github.com/YosysHQ/icestorm.git icestorm
cd icestorm
make -j$(nproc)
make install
```

# prjtrellis

Prjtrellis 是裝置的資料庫，用來產生最終要燒在裝置上的 bitstream，少了這個會導致下一步的 nextpnr 無法編譯。

```shell
git clone --recursive https://github.com/YosysHQ/prjtrellis
cd prjtrellis/libtrellis
cmake -DCMAKE_INSTALL_PREFIX=/usr/local .
make
```

# nextpnr

nextpnr 是開源的 FPGA 佈線工具，支援 Lattice 公司的 iCE40 和 ECP5 兩條產品線。  
這裡的指令是編譯 ECP5，可以換成 `-DARCH=ice40` 來編譯 iCE40 的 nextpnr。

```shell
git clone --recursive https://github.com/YosysHQ/nextpnr nextpnr
cd nextpnr
cmake . -DARCH=ecp5 -DCMAKE_INSTALL_PREFIX=/usr/local
make -j$(nproc)
make install
```

# SystemC

SystemC 是用來寫硬體的模型，會自己裝是因為 ubuntu 官方不附 cmake 的 FindPackage 檔，
這在用 Cmake 編譯 SystemC 的時候很煩。

```shell
wget https://github.com/accellera-official/systemc/archive/refs/tags/2.3.4.tar.gz -O systemc.tar.gz
tar zxf systemc.tar.gz
cd systemc-2.3.4
cmake -DCMAKE_INSTALL_PREFIX=/usr/local -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_STANDARD=17
make -j${NPROC} install
```

# Verilator

Verilator 作為開源的驗證工具已經算是品質最好的一個了，如果要玩開源硬體一定繞不過（除非你乾脆就不驗證了，笑你不敢）。  
之所以不用 ubuntu 官方的 package，是因為官方的版本不夠新，至少用 verilator v5.006 可以驗證 packed struct 比較方便。
```shell
wget https://github.com/verilator/verilator/archive/refs/tags/v5.006.tar.gz -O verilator.tar.gz
tar zxf verilator.tar.gz
cd verilator-5.006
autoconf
./configure --prefix=${THE_PREFIX}
make -j${NPROC}
make install
```

# 測試

測試用一個簡單的 [blink](https://github.com/YodaLee/icesugar-playground)。

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

用我們剛剛安裝的工具們來編譯：

```shell
yosys -p "synth_ecp5 -json blink.json" blink.v
nextpnr-ecp5 --25k --package CABGA256 --speed 6 --json blink.json --textcfg blink_out.config --lpf blink.lpf
ecppack blink_out.config blink.bin
```

就能產出可燒錄的 .bin 檔了。

# Put it all together

講了那麼多沒意思，直接提供 Dockerfile 好像比較實在~~Talk is cheap. Show me the Dockerfile~~
：
[ubuntu-icestorm-toolchain](https://github.com/yodalee/ubuntu-icestorm-toolchain)

載下來 docker build 一下，就能開始開發 Lattice FPGA 啦。
