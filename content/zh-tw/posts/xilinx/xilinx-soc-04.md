+++
author = "Yu-Sheng Lin"
title = "從零開始的 Xilinx SoC 開發（四）"
date = "2021-08-20"
description = "從零開始的 Xilinx SoC 開發（四）"
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

上幾篇文章中，我們把 FPGA 上所需要的元件都建立起來了，這篇將會把這些元件接起來，而在下一篇中，將會編譯出 bitstream，作為系列文前半部的收尾。

<!--more-->

### 連接元件

在我們建立這些元件的時候，可以看到上面會跳出 Run Coonection Automation 這個功能（圖上綠色部份），這邊我們將會使用這功能來完成 SoC 的連線，避免 clock reset 等信號拉錯產生的 bug。

<img src="/post_images/xilinx-soc/062-name.png" width="500" class="default-insert" />

此外，其實這個功能也隱藏在右鍵選單中。

<img src="/post_images/xilinx-soc/071-auto-connection.png" width="300" class="default-insert" />

在此之前，我有先把兩個 AXI Interconnect 的元件命名成 `axi_ic_control` 以及 `axi_data_control`，分別是 1 master + 1 slave 以及 1 master + 2 slave。

打開這個選單之後，我們先設定 CPU 的部份，也就是最下方的 slave 界面。因為連線時很多參數會相互影響，所以建議一次只連接少數的線。

首先因為這是 PL side 要跟 PS side 拿資料的界面，我們透過 `axi_ic_data` 把這個 slave 跟 CDMA 的 AXI 連起來。預設的 clock 都是 Auto，預設都會連接到 CPU 出來的 100MHz `pl_clk`，不過為了保險起見，還是全部用手動設定的。

<img src="/post_images/xilinx-soc/072-connect-cpu.png" width="600" class="default-insert" />

**按下 OK 之後**，重新回到這個界面。接著看到上方 DMA 跟 control 的部份，這兩個沒什麼可以設定的，所以就把全部的 clock 都手動設定成 `pl_clk`。

<img src="/post_images/xilinx-soc/073-connect-dma.png" width="600" class="default-insert" />

**再次按下 OK 之後**，重新回到這個界面。現在 DRAM 已經沒什麼好設定的了，稍微瀏覽檢查一下之後，除了 `sys_rst` 全部打勾就好。

<img src="/post_images/xilinx-soc/074-connect-ddr.png" width="600" class="default-insert" />

DRAM 的晶片因為不在 FPGA 上，所以這步設定 DRAM 的動作就是把 DDR 的信號線拉到 SoC 外側。此外，`sys_rst` 可以 tie-low 就好，所以這邊不做連線，等一下的步驟中才會設定。這些步驟做完之後，這個 SoC 應該會長這個樣子。

<img src="/post_images/xilinx-soc/075-system.png" width="800" class="default-insert" />

可以看到，在自動連接的過程中，Vivado 會自動幫我們加上 Processor System Reset 這個元件，他是是為了確保 reset 的順序正確。如果不是用自動的方式連線，就必須自己加上這個元件，相當麻煩。

### 設定 Slaves 的 Addresses

還記得前面我們建立了兩個 interconnect 嗎？這個步驟中，我們要把這兩個 interconnect 上的 slave 分別指定可以用來存取他們的 address。為此，我們切換到 Address Editor 頁面，把需要使用到的 slave 們右鍵 **Assign** 一個 addreess，沒有用到的用右鍵 **Exclude** 掉。

<img src="/post_images/xilinx-soc/076-assign-address.png" width="800" class="default-insert" />

照上面圖片設定，我們的兩個 interconnect 的 slaves 的 address 設定是這樣：

* Interconnect 1
	* Master
		* PS CPU 控制界面
	* Slave
		* DMA 控制界面：從 2GB 位置 (`0x8000_0000`) 開始算起 64KB
* Interconnect 2
	* Master
		* DMA 資料界面
	* Slave
		* PS DRAM 資料：從 0GB 位置 (`0x0`) 開始算起 2GB
		* PL DRAM 資料：從 4GB 位置 (`0x1_0000_0000`) 開始算起 4GB

這邊補充說明一下為什麼是這樣設定，參考 *Zynq UltraScale+ Device Technical Reference Manual* (UG#1085)，可以看到從 PS side 開出去的第一個 master port (`M_AXI_HPM0_LPD`)，必定只能從 `0x8000_0000` 開始，這決定了 interconnect 1 的 DMA 控制界面的位置（因為也只有一個 slave，所以就從頭開始 assign）。

另外，起始 2GB 是 DDR Memory Controller，CPU 可以看到的記憶體中，也就是說實體 DRAM 的前 2GB 會放在這邊。要讓 PS side 的 DMA 存取這塊的話，在這個 SoC 上，規定 DMA 跟 CPU 必須使用一樣的 address，所以我們也就只能把 interconnect 2 的 `0x0` 開始算起 2 GB 畫給 PS DRAM。而因為剩下的 4GB PL side DRAM 空間，其開頭必須跟 4GB 對齊，所以就只能從 4GB 位置 (`0x1_0000_0000`) 開始。

<img src="/post_images/xilinx-soc/077-system-address.png" width="800" class="default-insert" />

### 收尾

最後，我們要調整一下一些無法自動設定的部份，首先對左側對外拉出來的 DDR clock 信號線點兩下。

<img src="/post_images/xilinx-soc/081-ddr-port-clock.png" width="300" class="default-insert" />

他的頻率是預設的 100MHz，這個這定是錯的，要把 DDR 的元件設定打開，把這邊的頻率手動抄上去。

<img src="/post_images/xilinx-soc/082-ddr-clock.png" width="800" class="default-insert" />

另外，剛剛我們有提到 `sys_rst` 可以 tie-low 就好，因此我們要用內建的 Constant 元件把這條信號設定成 0。

<img src="/post_images/xilinx-soc/083-constant.png" width="300" class="default-insert" />

點兩下，把信號設定成 `1'b0`。

<img src="/post_images/xilinx-soc/084-constant-ddr.png" width="600" class="default-insert" />

接著連接到 DDR 元件的 `sys_rst`。

<img src="/post_images/xilinx-soc/085-constant-ddr-connect.png" width="300" class="default-insert" />

另外，根據 AXI protocol，AXI 會有對資料的保護機制、以及快取機制，這些對 DMA 要直接存取 PS side 的資料都是不方便的功能。這些功能是由 `arprot`/`awprot`/`arcache`/`awcache` 控制的，所以我們要加入**另外兩個** Constant 來關閉這個功能，具體可以看[官方文件](https://xilinx-wiki.atlassian.net/wiki/spaces/A/pages/1027702787/Linux+DMA+From+User+Space+2.0)中的設定，要把兩個 `prot` 結尾的信號設定成 `3'd2`，兩個 `cache` 結尾的信號設定成 `4'd11`，設定完成之後會變成如下圖這樣。

<img src="/post_images/xilinx-soc/086-constant-slave.png" width="500" class="default-insert" />

最後，我們把 CDMA interrupt 的 interrupt 拉回 CPU 就完成了（圖中淺綠色的線）。

<img src="/post_images/xilinx-soc/087-interrupt.png" width="700" class="default-insert" />

### 結論

我們終於把硬體的部份設定完成了，下一章中將編譯出 bitstream，完成 FPGA 本教學的第一階段。
