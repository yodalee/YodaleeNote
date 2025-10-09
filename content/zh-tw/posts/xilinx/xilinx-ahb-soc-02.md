+++
author = "Yu-Sheng Lin"
title = "在 Xilinx SoC 上放上自己的 IP（二）"
date = "2021-09-18"
description = "在 Xilinx SoC 上放上自己的 IP（二）"
featured = false
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

本篇文章接續了上一篇系列文的內容，將會把一個自己寫的 Verilog IP 放到 Xilinx FPGA 的 SoC 上。

<!--more-->

### 指定 AHB Slave 的 Address

在 create AHB IP 的最後一步驟中，我們必須設定 AHB Slave 的 address，告訴 SoC 這個 slave 的 address 空間有多大。為此，切換到 *Addressing and Mapping* 分頁下，一開始的空白頁面下，應該會顯示 *Run the Addressing and Memory Mapping Wizard to add a Memory Map or Address Space to Your IP*，這邊就直接 next next finish 按到底，中間記得選一下我們的 slave 就好。

做完之後，我們應該會在這個分頁下面有一個 entry，對他點右鍵 *Add Address Block*。

<img src="/post_images/xilinx-ahb/010-add-block.png" width="320" class="default-insert" />

預設會如下圖自動分配一個 4KB 的空間，對大多數的簡易 IP 控制界面來說，這個空間很夠用了。我們就按下最後的 *Review and Package* 一路 yes 到底就好了。

<img src="/post_images/xilinx-ahb/011-assigned.png" width="450" class="default-insert" />

### 回到 SoC 設計

接著，我們回到 SoC 的頁面拉出下述三個方塊並且互相連接，由於前面有[系列文](/series/%E5%BE%9E%E9%9B%B6%E9%96%8B%E5%A7%8B%E7%9A%84-xilinx-soc-%E9%96%8B%E7%99%BC/)講過怎麼做這些事情了，所以這邊只簡單條列要做的事情。

1. 把 CPU 開出一個 master port，例如說 `M_AXI_HPM0_LPD`。
1. 新增 *AXI AHBLite Bridge* 跟我們新增的 IP。
1. 把上述三者串連起來，這時應該會如下面第一張圖所示。
1. 用自動連線功能把 clock 全部連接起來，如下面第二張圖所示。
1. 對 AHB slave 指定一個我們希望的 address，如果是用 `M_AXI_HPM0_LPD` 的話，預設會放在 `0x8000_0000`。

<img src="/post_images/xilinx-ahb/012-block-diagram.png" width="650" class="default-insert" />

<img src="/post_images/xilinx-ahb/013-connect-clock.png" width="250" class="default-insert" />

最後，有一點詭異的地方要手動處理一下，這邊我不知道是 Vivado 的 bug 還是我沒有選到正確的設定。如果我們把兩邊 AHB 的信號點開，可以發現兩邊叫做 `HREADY` 的信號線都是 input，而且 master 端沒有 `HREADYOUT` 跟 `HSEL`。這是因為這 master 跟 slave 中間必須有一個 bus 來提供這些信號線，但是 Vivado 2020.2 並沒有提供 bus 的 IP。

幸好，在 master 跟 slave 是一對一的情形下，我們可以透過把 slave 的 `HREADY` 跟 `HSEL` 都設定成 `1'b1`，並且把 slave 的 `HREAYOUT` 接上 master 的 `HREADY`，如下圖所示：

<img src="/post_images/xilinx-ahb/014-connect-hready.png" width="550" class="default-insert" />

### 結論

這篇文章完成之後，就可以編譯出含有我們自己的 IP 的 bitstream 了，並且也能匯出 xsa 給 PetaLinux 使用。下一篇文章中，將會說明怎麼寫一個程式去操作這個 IP。
