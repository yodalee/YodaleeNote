---
title: "使用 Xilinx 開發板：連接 AXI Lite"
date: 2026-04-06
categories:
- FPGA
tags:
- Xilinx
- Vivado
series:
- XilinxBoard
---

故事是這樣子的，[之前說到]({{< relref "2025_hayashi">}})強者我同學給了我一些 Pynq AHB 
相關的文章，最近忙完一個階段重新開始改稿，發現只有那一篇好像有點乾，就決定把它擴展一下。
<!--more-->

目前規劃應該會寫個四篇：
1. 連接 AXI Lite
3. 連接 AHB
2. 連接 AXI Stream
3. 連接 Interrupt

文章會以 PynqZ2 開發板作為目標，這塊板子算 Pynq 系列中的初階板子，[官網價格](https://www.amd.com/zh-tw/corporate/university-program/aup-boards/pynq-z2.html)
大概 4000 多，如果寫硬體想要真的上 FPGA 板，是個不錯的入手對象，先前在 COSCUP 聽到實作 RiscV 核心也是
[用 Z2 來 demo](https://hackmd.io/@sysprog/HyjiP43N0)。  
比起之前介紹的 Lattice [icesugar-pro](https://yodalee.me/2021/08/openfpga_blink/)
，Xilinx 的板子在支援上也更強大，資源更多。

# Vivado

Vivado 是 Xilinx 官方提供的 FPGA 開發工具，相當於 Altera 的 Quartus II，用來進行
 RTL 合成、FPGA 佈線與生成 bitstream。  
[下載 Vivado](https://www.xilinx.com/support/download.html) 
需要先去 AMD (Xilinx) 註冊一個帳號，免費的帳號就夠了；安裝過程中在 device 欄位記得勾選 Zynq-7000。  

要提醒一下裝 Vivado **會吃掉一大把硬碟空間**，保守估計都是 **40-50 GB** 
起跳，如果硬碟空間不夠的話就買新的硬碟，像我的筆電 C 槽就只有 128GB 結果裝不了 
Vivado，裝完 C 槽直接變成紅色的。  
至於在安裝作業系統上，Windows 當然是不用說；Linux 的話我試過 Ubuntu 和 Archlinux，兩者在使用上都沒有問題。

# Pynq-Z2 介紹

Pynq-Z2 上面的處理器是 Xilinx Zynq-7000 SoC 的開發板，Zynq 系列的特點是 SoC 上整合一顆 CPU 與一顆
FPGA，分別稱為 *PS side* 與 *PL side*，在 Z2 上兩者分別為：
* PS (Processing System)：ARM Cortex-A9
* PL (Programmable Logic)：Artix-7 FPGA

一般的 FPGA 在使用時，是把 bitstream 燒錄到 FPGA 上的 flash，FPGA 在上電的時候會自動載入
flash 中的 bitstream。  
於是在進行開發時，測試不同的專案就要重新燒錄一次 flash，並備好什麼波形產生器、邏輯分析儀，
接一堆線才能開始除錯硬體，就好像換一個作業系統就要重灌電腦一樣。  
在 Pynq 上，PS 宛如開機碟一樣，可用軟體選擇要將哪個 bitstream 載入 PL，隨後利用 AXI 匯流排與
 PL 溝通，存取硬體資源或是控制硬體行為。  
Z2 預設的映像檔中包含 Linux 作業系統和開機後自動執行的 Jupyter 
Notebook，開好機就能使用 pynq 提供的載入燒錄 bitstream 檔，這讓我們進行硬體測試時方便許多。  


拿到 Z2 之後設定方式請參考[官方 Setup Guide](https://pynq.readthedocs.io/en/v2.6.1/getting_started/pynq_z2_setup.html)。  

安裝完 Vivado 之後，預設沒有 Z2 板子的支援，可以從 [TUL 的官網](https://www.tulembedded.com/FPGA/ProductsPYNQ-Z2.html)
上找到[下載連結](https://dpoauwgwqsy2x.cloudfront.net/Download/pynq-z2.zip)。  
安裝方式可參照 [Board Setting](https://pynq.readthedocs.io/en/v3.1/overlay_design_methodology/board_settings.html)
的描述，解壓縮後丟進路徑
```txt
<Xilinx installation directory>/Vivado/<version>/data/xhub/boards/XilinxBoardStore/boards/Xilinx/
```
即可。

# 建立 Vivado Project

安裝好 Vivado 之後，在 Vivado 中新增我們第一個專案：
* Create Project 指定 Project Name 和 Locations
![Create Project](/images/xilinx/AXILite_0projectname.png)
* Project Type 指定為 RTL Project
* Default Parts 在 Boards 選擇安裝的 pynq-z2
![Pynq Z2](/images/xilinx/AXILite_1board.png)

這樣就會生出一個空白的 project 了。

# 建立 AXI Lite Slave IP

在 Zynq 架構中，最常見的一種控制介面就是 AXI Lite，很適合做最基本的 IP CSR 的寫入與讀取。  
我們這裡的範例是一個很簡單的模組：
* reg0：輸入 32 bits 整數 A
* reg1：輸入 32 bits 整數 B
* reg2：輸出 32 bits 整數 C = A + B

在 Vivado 建立一個 AXI4-Lite Slave IP，流程如下：
* Tools -> Create and Package New IP
* 選擇 Create a new AXI4 Peripheral
![AXI Peripheral](/images/xilinx/AXILite_2CreateIP.png)
* Peripheral Detail 填入模組的資訊，以下叫這個 module 為 AdderWrapper
![IP detail](/images/xilinx/AXILite_3IPdetail.png)
* Add Interfaces 維持原樣，一個 AXI Lite 模式選擇為 Slave，Register 數設定為 4 即可，如果設計很大這裡可以設到 512 個 registers。
![AXI Interfacel](/images/xilinx/AXILite_4Interface.png)
* Create Peripheral 可以選擇 Add IP to the repository 然後先連接 block design；也可以選 Edit IP 編輯 IP。

## 編輯 AXI Lite IP

打開 AdderWrapper 之後，可以看到 Vivado 生成的 code
1. 最上層的 AdderWrapper.v
2. 下層的 AXILite Handler：AdderWrapper_slave_lite_v1_0_S00_AXI.v，以下簡稱 S00_AXI.v。

Vivado 的設計邏輯是這樣子的：
> AdderWrapper 提供了 AXI Lite 的介面，這批訊號整個灌進 AXILite Handler，在裡面存取 AXI Lite 暫存器。

S00_AXI.v 就是一個 AXI interface 實作，除了 parameter 多了些，其他還算好懂，想要熟悉
 AXI protocol 的也很推薦從這個模組上手。  
簡單說 AXI 由五組獨立的通道所組成：AW、AR、W、R、B，每組通道都是由 valid/ready 控制，傳輸對應的資料。  
寫入的時候，由 AW 通道傳輸寫入位址，存到 axi_awaddr 變數；W 通道寫入資料到 slv_reg；B 通道回傳寫入的結果。  
讀取的時候，由 AR 通道傳輸讀取位址，存到 axi_araddr 變數；R 通道回傳讀取的內容 axi_rdata 和 reg_data_out。  

雖然沒有明說，不過我這裡的改動會是這樣：
1. 把你要連接的模組 Adder.v 放在 AdderWapper.v
2. 所有連接的線路宣告 wire 在 AdderWrapper.v，並成為 S00_AXI.v 的 port
3. 在 S00_AXI.v 中將這些線路接上 S00_AXI.v 提供的暫存器

畫成圖會像這樣：

![AXI Handler Wiring](/images/xilinx/AXILite_5Wiring.png)

Adder.sv 的內容如下：
```systemverilog
module Adder (
  input [31:0] a,
  input [31:0] b,
  output [31:0] c
);
assign c = a + b;

endmodule
```

新增方法為：
* File -> Add Sources -> Add or create design sources -> 選擇 Adder.sv
* 宣告 a, b, c 三條寬度為 32 bits 的線
* 在 AdderWrapper.sv 中實例化 Adder.sv
* 在 S00_AXI.v 的介面上宣告 a, b, c 的埠，注意埠的方向跟 Adder.sv 會是相反的，因為對 
Adder.sv 的 input 是從 S00_AXI.v 中 register 儲存的內容，所以在 
S00_AXI.v 上會是 output port。
* 在 S00_AXI.v 中，將 slv_reg0, slv_reg1 賦值給 a, b；將 c 寫入到讀取 offset 2 時的 reg_data_out 值。

收尾，點選左邊的 Edit Packaged IP，一路點到最後，按 Re-Package IP 就完成 IP 的封裝了

# 連接 Block Diagram

## 1 建立 Zynq Processing System
選擇 Vivado 的 Create Block Design，Design name 一般就取 design_1。
1. 在 Block Diagram，使用 Add IP 加入 ZYNQ7 Processing System
2. 使用 Run Block Automation，讓 Vivado 自動完成 DDR 和 FIXED_IO

如果出現 Run Block Automation 幾乎是標準流程，交給 Vivado 處理就好。

## 2 加入自訂 AXI Lite IP

從 IP 列表中找到你寫的 AdderWrapper 將它加到 Block Diagram，一樣使用
 Run Block Automation，Vivado 會自動叫出 AXI Interconnect 模組以及 Reset 模組。  
AXI Interconnect 就是 AXI 匯流排的交換器，可以在上面接上多個 master 與 slave，AXI 
interconnect 會負責進行仲裁、地址解碼等工作，此處使用 1 master 1 slave 的 AXI Interconnect 即可。

## 3 收尾

完成後，整個 Block Diagram 通常會包含：
* Zynq PS
* AXI Interconnect
* 自訂的 AXI Lite IP
* Clock / Reset 模組

![AXILite Block diagram](/images/xilinx/AXILite_6Block.png)

這時候 PS 就已經能透過 AXI Lite 存取你設計的硬體模組了，最後一步是在專案階層的 
design.bd 上點右鍵，選擇 *Create HDL Wrapper*，這個 
wrapper 檔內就會包含所有你畫的模組和它們的 verilog code。  
後面我們在 AXI Stream 的章節，會遇到需要檢視這個檔案才成功除錯的問題，
但一般除非例外，不然都不需要去檢視生成的~~嘔吐物~~ verilog code 才對。

# 上板測試

## 產生 bitstream

設計完成後，接下來就是把它跑在板子上。與下晶片一樣，Vivado 會經過下面幾個步驟：

1. Synthesis：將 RTL 合成為邏輯閘與暫存器，在 FPGA 上的合成的目標會是 
LUT (Look-up table) 和 FF (flip flop) 等基本元件。
2. Implementation：將合成的結果佈局到選擇的 FPGA 型號上面。
3. Generate Bitstream：將佈局結果寫出為 bistream 檔以燒錄到 FPGA 上

Generate bitstream 完成之後，會需要兩個檔案：
* .bit 檔，在 `<Project Name>.runs/impl_1/` 下，這就是要燒進 FPGA 的 bitstream 檔案
* .hwh 檔，hwh 是指 hardware handoff file，這是告訴 zynq 的 PS 系統，要怎麼跟這個硬體溝通，在
`<Project Name>.gen/sources_1/bd/design_1/hw_handoff/` 下

因為太麻煩我都是用尋找副檔名 .bit .hwh 的方式去找。  
兩個檔案名字通常會不一樣，一個是 block diagram .bd 的名字，一個是
 HDL wrapper 的名字，先把他們改成一樣的名字，以下統一叫 
 AdderWrapper.bit 跟 AdderWrapper.hwh。

## Jupyter Notebook 測試

把 .bit 與 .hwh 上傳到 jupyter notebook 中，開啟一個新的 python3 檔案。  

以下是操作時的 python 程式碼與截圖，pynq 與 Overlay 的實作是 
Xilinx 官方提供的套件，讓我們能動態的載入想要測試的 .bit 檔。  
由於我們把 Adder 模組的 A, B, C 放在 register 
0, 1, 2，對應到 AXI 上的位址就是 0x0, 0x4 和 0x8。

```python
from pynq import Overlay
img = Overlay("AdderWrapper.bit")
img?
img.AdderWrapper_0.write(0x0, 0xdead)
img.AdderWrapper_0.write(0x4, 0xbeef)
print(hex(img.AdderWrapper_0.read(0x8)))
assert img.AdderWrapper_0.read(0x8) == 0x19d9c
```

![Jupyter Notebook](/images/xilinx/AXILite_7JupyterNote.png)

# 結語

Pynq-Z2 是一張 Zynq 架構的入門開發板，透過 Vivado + AXI Lite 可以建立 SoC
 FPGA，在軟體端快速載入不同的 IP 進行測試與驗證。

結束了 AXI lite 之後，下一章我們先回到比較低階的 AHB bus，看看要怎麼在
 IP 中設置不同的介面，並與 verilog 中的埠對接。
