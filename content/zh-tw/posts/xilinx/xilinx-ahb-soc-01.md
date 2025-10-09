+++
author = "Yu-Sheng Lin"
title = "在 Xilinx SoC 上放上自己的 IP（一）"
date = "2021-09-11"
description = "在 Xilinx SoC 上放上自己的 IP（一）"
featured = true
tags = [
   "xilinx",
   "vivado",
]
categories = [
   "tool",
   "technical",
]
series = ["在 Xilinx SoC 上放上自己的 IP"]
aliases = []
math = false
+++

前面幾個系列中，我們在 Xilins FPGA 上面建立了 SoC，然而並沒有提到需要自己寫 Verilog IP 的部份。在很多時候，會想使用 FPGA 是因為我們需要的是在上面放上自己用 Verilog 開發的的 IP，跟 SoC 一起運作，FPGA 執行我們需要的加速功能。這系列的文章中，將會說明怎麼自己寫一個簡單的 Verilog，包裝成可以放在 SoC 裡面的 IP，並讓 PetaLinux 可以存取。

<!--more-->

### 我們的 AHB IP

在文章正式開始之前，我們先來說一下，所謂簡單的 Verilog IP 是要執行什麼功能，下面這段程式碼裡實做了一個 AHB 的 IP，具有 AHB IP 標準的 IO port，他的唯一功能就是在被讀取的時候，會讀出 `32'h55665566` 的值。

{{< highlight verilog >}}
module MyGoodAhbModule(
   input clk,
   input rst,
   input               HSEL,
   input  [7:0]        HADDR,
   input  [1:0]        HTRANS,
   input  [2:0]        HSIZE,
   input               HWRITE,
   input  [31:0]       HWDATA,
   input               HREADY,
   output logic        HREADYOUT,
   output logic [31:0] HRDATA,
   output logic        HRESP
);
   assign HRESP = 1'b0;
   assign HREADYOUT = 1'b1;
   assign HRDATA = 32'h55665566;
endmodule
{{< /highlight >}}

至於如果讀者對 AHB 不熟悉，看不懂上面的 module 在寫什麼的話，上網搜尋 AHB 的 specification 可以很容易找到。

### 打包 AHB IP

我們的目標是，要把上面這個 IP 打包成一個可以放在 block design 裡面，並且可以跟 SoC 連結。首先我們要打開 Vivado 的 *Create and Package New IP* 選單。

<img src="/post_images/xilinx-ahb/001-create-ip.png" width="400" class="default-insert" />

打開之後，因為這只是做個 prototype，所以我們選取最簡單的方法，把上面的 Verilog 檔案放在一個單獨的資料夾下（建議放在同一個 project 下面的資料夾）。在這個步驟中，選取 *Package a specified directory* 選項，並選取該資料夾。

<img src="/post_images/xilinx-ahb/002-specify-directory.png" width="650" class="default-insert" />

一路 next next 到底之後，會開出一個新的暫時的 Vivado project，其中第一件重要的事情是檢查我們所有的 IO port。而最後的目的是在這個界面中告訴 Vivado，此 module 的哪些 IO port 會哪些對應到 AHB 的哪些信號。被對應到的信號會被縮起來，並且用 `>` 顯示，例如圖中的 `Cloak and Reset Signals` 就是已經完成對應的信號了。

<img src="/post_images/xilinx-ahb/003-list-signals.png" width="650" class="default-insert" />

接著，我們要把那些 `H` 開頭的信號對應到 AHB，因此我們點頁面的加號（或是右鍵 `Add Bus Interface`）。因為我們要建立一個 AHB slave，所以在 *General* 分頁中，我們在 *Interface Definition* 選取 `ahblite_rtl`，*Name* 用喜歡的就好了， *Mode* 設定為 slave。

<img src="/post_images/xilinx-ahb/004-create-ahb.png" width="600" class="default-insert" />

（注意：在 2020.2 版本中，`ahblite_rtl` 有兩個，這邊要選有 `HREADY_IN` 跟 `HREADY_OUT` 兩個信號的那個。）

接下來我們進到 *Port Mapping* 頁面，把一個個的 port 對應起來，這邊我們在左右想要對應的 port 各點一下，按下 *Map Ports* 就好。因為這個 Verilog code 中，都照 AHB 規範命名，總之就是把全部名字一樣的 map 起來就對了。

<img src="/post_images/xilinx-ahb/005-map-port.png" width="500" class="default-insert" />

這邊有兩點要稍微注意一下：
1. 在大多數 AHB 文件標準中，`HREADY_IN`、`HREADY_OUT` 是叫做 `HREADY`、`HREADYOUT`，名字有點不同。
1. `HPROT`、`HMASTLOCK`、`HBURST` 沒有被對應到，這些在簡單的 AHB slave 中一般也很少用到，是 optional 的信號。

### 完成 IP（的前半）

這個步驟做完之後，本來 `Ports and Interfaces` 的頁面應該會變得很乾淨：

<img src="/post_images/xilinx-ahb/006-mapped-port.png" width="400" class="default-insert" />

注意有的時候，clock 跟 reset 兩個信號線不一定會被自動辨認。在這個情形下，我們必須自行用同樣的方法，新增 `clock_rtl` 跟 `reset_rtl` 兩個 slave，然後把 port map 上去。

最後，我們把 AHB slave 跟 reset 都右鍵 `Associate Clocks`，告訴 Vivado 說這些信號是對齊 clock signal 的，這樣我們就**快**完成了（嗯對，還沒完成）。

<img src="/post_images/xilinx-ahb/007-associate-clock.png" width="300" class="default-insert" />

### 結論

到這邊為止我們還沒完成 IP 的打包，因為還有 `Addressing and Memory` 的頁面要設定才能完成 IP 打包，不過因為文章有點長了，所以就留待下篇吧。
