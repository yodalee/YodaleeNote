+++
author = "Yu-Sheng Lin"
title = "從零開始的 Xilinx SoC 開發（一）"
date = "2021-08-07"
description = "從零開始的 Xilinx SoC 開發（一）"
featured = true
tags = [
    "xilinx",
    "vivado",
]
categories = [
    "tool",
    "technical",
]
series = ["從零開始的 Xilinx SoC 開發"]
aliases = []
math = false
+++

許多現代的 FPGA 上都配有 ARM A 系列 CPU（像是 A53, A9）以及 DRAM，上面可以執行 Linux 作業系統。而自己寫的 Verilog 則是透過 bus 和 CPU 相連，SoC 的方式。因此在 FPGA 上開發 SoC 來說，完整的 flow 需要相當多的知識。本系列文章紀錄了一個幾乎沒碰過 FPGA 開發的工程師，使用 Xilinx UltraScale+ FPGA 的開發筆記。這邊聲明一下，本文雖然標題是從零開始，但是畢竟作者自己也是電機背景出身，FPGA, Verilog 也是算熟悉，對 SoC 也有基本程度的知識，平時就用 Linux 當主要工作用 OS，所以也不是說完全從零開始。

<!--more-->

### 先建立 SoC

既然都是從零開始，那麼就從打開 Vivado 說起吧，首先在 create new project 之後，我們就會一連串的按下 next next next、選取要把 project 放在哪個資料夾，接著大多都會卡在選取 FPGA 這步，如果是買 Xilinx 官方的 UltraScale+ 像是 ZCU102 等等，直接從這邊選一個就對了。

<img src="/post_images/xilinx-soc/000-new-project-board.png" width="500" class="default-insert" />

如果是買第三方或是客製化的 FPGA 板，請自己去第三方的網站找 example，或是去問設計廠，在這邊要選哪個選項。

<img src="/post_images/xilinx-soc/001-new-project-fpga.png" width="500" class="default-insert" />

接著，我們的目標便是建立一個簡單的 SoC，裡面使用了這些元件，並且這個 SoC 要可以執行我們自己建立的 Linux：

* CPU 側（又稱 PS side）
	* CPU 本身
	* DRAM
* FPGA 側（又稱 PL side）
	* DRAM
	* DMA，可以在兩個 DRAM 之間搬運資料。

注意到許多的 Xilinx FPGA 上，PS side 以及 PL side 都有各自的 DRAM，兩邊是獨立設定的。

### Vivado

為了建立上述的 SoC，建立 project 之後，第一個步驟就是點開 Create Block Design 來建立 SoC。

<img src="/post_images/xilinx-soc/010-create.png" width="400" class="default-insert" />

建立SoC之後，不意外的是一片空白，什麼都沒有的界面。

<img src="/post_images/xilinx-soc/011-empty.png" width="800" class="default-insert" />

首先，我們把 UltraScale+ 本身的 CPU 加入這個 SoC 裡面，右鍵 Add IP（或是按 GUI 的加號），接著搜尋 zynq 就可以找到 Zynq UltraScale+ MPSoC 了，這樣的系統本身包含了。這邊要稍微注意一下，如果不是 UltraScale+ 的 FPGA，MPSoC 的名字跟長相會不太一樣。

<img src="/post_images/xilinx-soc/012-add-cpu.png" width="800" class="default-insert" />

這個版本的 Vivado 中，剛加入的 UltraScale+ 的 CPU default 會保留有一個 AXI master 界面 (`M_AXI_HPM0_LPD`)，讓我們可以 access 對外的 AXI slave。

<img src="/post_images/xilinx-soc/021-default-cpu.png" width="400" class="default-insert" />

接著直接按下上方工具列的 Validate Design（或是 F6），就會出現像是下面的 error message，告訴我們 SoC 有錯誤，這是因為 `M_AXI_HPM0_LPD` 那個 master 沒有連接到對應的 clock，也就是左側 `maxihpm0_lpd_aclk`。

<img src="/post_images/xilinx-soc/022-verify.png" width="400" class="default-insert" />

所以我們對 CPU 點兩下，進入 PS-PL Configuration 裡面，把這個 master 取消掉。

<img src="/post_images/xilinx-soc/023-uncheck.png" width="400" class="default-insert" />

現在的 CPU 長下圖這樣，可以看到 `M_AXI_HPM0_LPD` 跟 `maxihpm0_lpd_aclk` 都不見了，這時再按下 F6，就不會出現剛剛的 error 了。
<img src="/post_images/xilinx-soc/024-less-cpu.png" width="300" class="default-insert" />

### 結論
讀到了這邊這篇文章就到這邊結束了，有沒有發現一個問題呢？就是這篇根本沒有講到 PL side，連 PS side 的 DRAM 都沒有提到。沒有錯，就是因為我懶得打了！因此下幾篇中，將會說明如何正確設定 CPU, DRAM 以及拉出正確的 SoC。
