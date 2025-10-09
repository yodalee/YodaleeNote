+++
author = "Yu-Sheng Lin"
title = "從零開始的 Xilinx SoC 開發（二）"
date = "2021-08-10"
description = "從零開始的 Xilinx SoC 開發（二）"
featured = false
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

上一篇文章展示了 FPGA 的 SoC 的 GUI 的基本操作，在這篇文章中，我將會說明如何設定 FPGA 上 PS side 的 CPU 以及 DRAM。

<!--more-->

### 前情提要

在上一篇文章中，我們最終的目標是執行一個 Linux，上面可以使用到這些元件：

* CPU 側（又稱 PS side）
	* CPU 本身
	* DRAM
* FPGA 側（又稱 PL side）
	* DRAM
	* DMA，可以在兩個 DRAM 之間搬運資料。

然而實際上，上一篇並沒有使用 PL side 的任何東西，也沒有提及 PS side 的 CPU 以及 DRAM 的設定，因此在本篇中，將會著重在 PS side 的必要設定。

### 設定 PS Side DRAM

首先，我們對 CPU 點兩下，進入 CPU 的設定頁面。在 PS side 的設定中，最會影響到運作正確性的是 DRAM 的時序設定。DRAM 的時序參數非常多，例如說 DRAM 的不同的讀寫指令的間隔要求等參數。

<img src="/post_images/xilinx-soc/031-dram.png" width="750" class="default-insert" />

不幸地，DRAM 的參數非常難設定，就如同一般 PC 超頻的玩家，在超頻 DRAM 時也要在 BIOS 裡面調整各種參數，才不會開機之後 BSOD，這也不是大多數會使用 FPGA 的工程師的專長。因此，最簡單的方法請自己去第三方的網站找 example，從右上角的 Presets 中匯出 CPU 的 tcl 設定檔，再套用到現在的 CPU 中。

<img src="/post_images/xilinx-soc/032-configure-again.png" width="750" class="default-insert" />

### 設定 PS Side CPU

相較於 PS side DRAM 的設定，PS side CPU 的設定就比較和藹可親（比較可讀）了，大多數情形下，套用了 preset 之後，唯一會需要動的是 PS-PL Configuration 這個 tab。

PS-PL Configuration 是設定 PS side 到 PL side 要保留哪些通訊界面，例如我們要讓 PS side CPU 可以存取 DMA，我們就需要讓 CPU 多一個 master 界面。類似地，如果我們要讓 DMA 可以存取 PS side DRAM，就要讓 CPU 多一個 slave 界面。

<img src="/post_images/xilinx-soc/033-ps-pl-configure.png" width="500" class="default-insert" />

為此，我們繼續進入 CPU 的設定頁面，在 PS-PL Configuration 這頁的設定中，打開各一個 master 以及 slave port。這邊兩個 port 的 Data Width 的設定不一樣，因為 master 是打算存取 DMA 用的，只保留了 32-bit 的界面就很足夠了；另一方面，slave 是要讓 DMA 搬運資料用的，因此使用了 128-bit 的界面。如此一來，我們的 CPU 現在應該長這個樣子。

<img src="/post_images/xilinx-soc/034-new-cpu.png" width="400" class="default-insert" />

至於為什麼是 `HPM0 LPD` 跟 `HPC0 FPD` 這兩個？不能選 其他 master 或是 slave 嗎？這是因為大部分的 example 都是選用這兩個，所以我就跟著使用了，我相信其他 port 應該也是會正確運作的。

### 結論

在這篇文章中，我們完成了 FPGA PS side 的設定，在下一篇中，將會開始進入 PL side 的部份。
