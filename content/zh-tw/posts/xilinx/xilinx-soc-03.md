+++
author = "Yu-Sheng Lin"
title = "從零開始的 Xilinx SoC 開發（三）"
date = "2021-08-19"
description = "從零開始的 Xilinx SoC 開發（三）"
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

上一篇文章中，我們設定了 FPGA 上 PS side 的 CPU 以及 DRAM，這篇文章中將會完成 PL side 的設定。（文章概要怎麼好像越寫越短了......）

<!--more-->

### 前情提要
在本系列的文章中，我們最終的目標是執行一個 Linux，上面可以使用到這些元件：

* CPU 側（又稱 PS side）
	* CPU 本身
	* DRAM
* FPGA 側（又稱 PL side）
	* DRAM
	* DMA，可以在兩個 DRAM 之間搬運資料。

上一篇中把 PS side 的 CPU 以及 DRAM 的設定，因此在本篇中，將會著重在 PS side 的必要設定，包括了 DRAM 以及 DMA。

### 新增必要元件

#### AXI Interconnect：CPU 對外溝通的橋樑
在之前畫出來的 SoC 中，我們只有把 PS side 的 CPU 跟 DRAM 放上去，在上一篇文章的最後，我們的 CPU 有一個 slave 跟 master 界面（左上以及右上）。

<img src="/post_images/xilinx-soc/034-new-cpu.png" width="400" class="default-insert" />

接下來的步驟中，我們將會新增必要的元件，讓 CPU 可以夠過這些界面存取。要讓 CPU 可以存取元件，最重要的是有中間橋樑讓 CPU 跟元件之間可以相互連結，為此我們必須使用 AXI Interconnect 這個元件，在這邊我們新增**兩個** AXI Interconnect。

<img src="/post_images/xilinx-soc/040-axi.png" width="300" class="default-insert" />

為什麼是兩個呢？上一篇文章我們提到在這個系統中，要讓 PS side CPU 可以存取 DMA，以及讓 DMA 可以存取 PS side DRAM。所以先來複習一下這個系統有哪些 master 跟 slave：

* Master
	* PS CPU 控制界面
	* DMA 資料界面
* Slave
	* PS DRAM 資料
	* PL DRAM 資料
	* DMA 控制界面

其實我們可以只用一個 Interconnect，有兩個 master 跟三個 slave，然後把所有的 master 跟 slave 都接上去，不過這樣會讓傳輸的信號相互干擾，所以這邊我選擇分離為兩個 Interconnect。

* Interconnect 1
	* Master
		* PS CPU 控制界面
	* Slave
		* DMA 控制界面
* Interconnect 2
	* Master
		* DMA 資料界面
	* Slave
		* PS DRAM 資料
		* PL DRAM 資料

#### DDR4 DRAM 以及 DMA

接著，我們先把剩下需要的元件加一加，首先加入 CDMA。在我用的版本的 Vivado 中，有兩種 DMA，這邊我們只是需要類似 `memcpy` 的功能的話，使用比較基本的 CDMA 就好。

<img src="/post_images/xilinx-soc/041-cdma.png" width="300" class="default-insert" />

另外，因為 UltraScale+ 是 DDR4 記憶體，所以我們加入 DDR4 的 controller。

<img src="/post_images/xilinx-soc/042-dram.png" width="300" class="default-insert" />

完成之後，現在的 block diagram 應該長這個樣子了：

<img src="/post_images/xilinx-soc/043-block-diagram.png" width="600" class="default-insert" />

### 設定元件
接下來我們將會設定每一個剛剛加入好的元件。

#### AXI Interconnect
首先，剛剛有提到，我們的 SoC 裡面，有兩個 AXI Interconnect，一個有 1 master + 2 slave，另外一個是 1 master + 1 slave，需要點開 AXI 的框框分別去作設定。

<img src="/post_images/xilinx-soc/051-config-axi.png" width="600" class="default-insert" />

#### PL Side DRAM
接著是 DRAM，基本上這邊沒有可以調整的部份，跟前面設定 PS side DRAM 的時候一樣，必須自己去第三方的網站找 example，把參數抄下來。可惜的是這邊沒有 tcl 設定檔可以用，因此請小心的注意每個 tab 的設定都有完美複製過來。

<img src="/post_images/xilinx-soc/052-config-dram.png" width="600" class="default-insert" />

#### PL Side DMA

最後，DMA 的部份，我們把全部的額外功能都關掉，因為用不到（預設只有 Enable Scatter-Gather 是開啟的）。接著，把 Write/Read Data Width 改成 128 跟上一篇文章的設定一致，並把 Address Width 改成 36。

<img src="/post_images/xilinx-soc/053-config-dma.png" width="600" class="default-insert" />

為什麼是 36-bit 呢？我們要 address 的總記憶體超過 4GB，因此原本的 32-bit 必定不夠用。此外，因為透過 slave 界面存取 PL side DRAM 時 (`S_AXI_FPC0_FPD`)，使用的是跟 CPU 一致的 memory address，參考 *Xilinx Userguide #1085 Zynq UltraScale+ Device Technical Reference Manual* 的 *System Address* 的這個章節，32-bit 模式只能存取到 DDR4 的前 2 GB，只有 36-bit 模式才能存取到完整的 PS side DRAM。因此方便起見，就保留了使用 36-bit。

### 改變顯示界面

這邊特別想提 Vivado 的 GUI 裡面有兩個有趣的功能，都是改變顯示在螢幕上的東西，並不影響任何功能，所以讀者也可以跳過這小節。然而這兩個功能還算實用，且一般的文件也不會特別去提，根本不知道有這個功能，才特別想說明一下。

第一個功能是改變元件的名稱，當我們點開設定時，會發現 Component Name 怎麼不能改，當元件一多起來會很難讀。

<img src="/post_images/xilinx-soc/061-name.png" width="600" class="default-insert" />

但是其實他是可以改的，只是要從側邊欄位去修改而已。

<img src="/post_images/xilinx-soc/062-name.png" width="600" class="default-insert" />

第二，線的顏色也是可以用右鍵選單的 highlight 改的。

<img src="/post_images/xilinx-soc/063-color.png" width="350" class="default-insert" />

### 結論
下一章中，我將會說明如何把這些元件接起來，也就是把硬體的部份設計完成。
