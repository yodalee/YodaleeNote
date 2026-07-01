---
title: "使用 Xilinx 開發板：連接 AHB"
author: "Yu-Sheng Lin, Yodalee"
date: 2026-04-28
categories:
- FPGA
tags:
- Xilinx
- Vivado
series:
- XilinxBoard
---

在上一篇，我們在 PynqZ2 上面建立了 SoC，並且能用 AXI Lite 介面去控制它，然而現實中使用 
AXI 其實是相對奢侈的；在比較簡單的實作上，會使用較簡單的 APB 或是 AHB bus。  
在這篇文章我們就來說明要怎麼實作並連接一個 AHB 的 IP，並讓 PS side 可以存取。 
<!--more-->

# 打包 AHB IP

## 實作一個 AHB 可讀可寫的模組

我們示範的模組是一個單純的 AHB，沒有任何 address，任何的寫入都會放進 
register 內，在讀取時會讀到位元反轉的結果。  
在這個年頭這種模組請 AI 幫忙寫就好了，以下是 prompt 與它的回覆：

> Help me implement an AhbCli module, that we can write a 32 bits value and read bit inversion of it.

```systemverilog
module AhbCli #(
    parameter ADDR_WIDTH = 32
)(
    input  logic                  clk,
    input  logic                  rst,

    // AHB-Lite slave interface
    input  logic                  HSEL,
    input  logic [ADDR_WIDTH-1:0] HADDR,
    input  logic                  HWRITE,
    input  logic [1:0]            HTRANS,
    input  logic [2:0]            HSIZE,
    input  logic [31:0]           HWDATA,

    output logic [31:0]           HRDATA,
    output logic                  HREADYOUT,
    output logic                  HRESP
);

// -------------------------
// Internal register
// -------------------------
logic [31:0] reg_data;

// AHB valid transaction
logic trans_valid;
assign trans_valid = HSEL && HTRANS[1]; // NONSEQ or SEQ

// -------------------------
// Write logic
// -------------------------
always_ff @(posedge clk or negedge rst) begin
    if (!rst) begin
        reg_data <= 32'h0;
    end else if (trans_valid && HWRITE) begin
        reg_data <= HWDATA;
    end
end

// -------------------------
// Read logic
// -------------------------
always_comb begin
    if (trans_valid && !HWRITE) begin
        HRDATA = ~reg_data;
    end else begin
        HRDATA = 32'h0;
    end
end

// -------------------------
// AHB response
// -------------------------
assign HREADYOUT = 1'b1; // always ready
assign HRESP     = 1'b0; // OKAY

endmodule
```

我們的目標是，要把上面這個 IP 打包成一個可以放在 block design 裡面，並且可以跟 SoC 連結。  

## 建立 AHB IP

首先我們要打開 Vivado 的 `Create and Package New IP` 選單。

![Create IP](/images/xilinx/ahb_001_create_ip.png)

因為這只是做個 prototype，所以我們用最簡單的方法，把上面的 Verilog 
檔案放在一個單獨的資料夾下（建議放在同一個 project 下面的資料夾）。  
在這個步驟中，選取 `Package a specified directory` 選項，並選取該資料夾。

![specify directory](/images/xilinx/ahb_002_specify_directory.png)

一路 next next 到底之後，會開出一個新的暫時的 
Vivado project，其中第一件重要的事情是檢查我們所有的 IO port。  
在 block diagram 中連接 IP 時，Vivado 自然不會知道 verilog 哪個 IO Port 是 AHB
address？哪個是 data？
打包 IP 的 `Ports and Interfaces` 分頁就是告訴 Vivado，此 
module 的哪些 IO port 會哪些對應到 AHB 的哪些信號。  
已對應的信號會被縮起來，並且用 `>` 顯示，例如圖中的 
`Clock and Reset Signals` 就是已經完成對應的信號了。

![list signals](/images/xilinx/ahb_003_list_signals.png)

我們要把那些 `H` 開頭的信號對應到 
AHB，因此我們點頁面的加號（或是右鍵 `Add Bus Interface`）。  

在 `General` 分頁中：
* `Interface Definition` 選取 `Advanced/ahblite_rtl`
* `Name` 用喜歡的名字
* `Mode` 設定為 slave

![create ahb](/images/xilinx/ahb_004_create_ahb.png)

在 Vivado 中，`ahblite_rtl` 有兩個，第二個多了 `HREADY_IN`, `HREADY_OUT`，
這是要讓多個 AHB Slave 互相溝通用的；為了讓 Vivado 在 
block diagram 裡面可以正常連線，這裡要選第二個。

接下來我們進到 `Port Mapping` 頁面，把一個個的 port 
對應起來，這邊我們在左右想要對應的 port 各點一下，按下 `Map Ports` 就好。  

![map port](/images/xilinx/ahb_005_map_port.png)

因為 Verilog code 幾乎照 AHB 規範命名，把全部名字一樣的 map 
起來就對了，不過還是有兩點要稍微注意一下：  
1. 在大多數 AHB 文件標準中，`HREADY_IN` `HREADY_OUT` 是叫做 
`HREADY` `HREADYOUT`，名字有點不同。
2. `HPROT` `HMASTLOCK` `HBURST` 沒有被對應到，這些在簡單的 
AHB slave 中一般也很少用到，是 optional 的信號。

這個步驟做完之後，本來 `Ports and Interfaces` 的頁面應該會變得很乾淨：

![mapped port](/images/xilinx/ahb_006_mapped_port.png)

> 有的時候，clock 跟 reset 兩個信號線不一定會被自動辨認。  
> 在這個情形下，我們必須自行用同樣的方法，新增 `clock_rtl` 跟 `reset_rtl`
> 兩個 slave，然後把 port map 上去。
{.error}

最後，我們把 AHB slave 跟 reset 都右鍵 `Associate Clocks`，告訴 Vivado 
指定這些信號是對齊這個 clock signal。

![associate clock](/images/xilinx/ahb_007_associate_clock.png)

## 指定 AHB Slave 的 Address

在 create AHB IP 的最後一步驟中，我們必須設定 AHB Slave 的 address，告訴 
SoC 這個 slave 的 address 空間有多大。  
為此，切換到 `Addressing and Mapping` 分頁下，一開始的空白頁面下，應該會顯示 
`Run the Addressing and Memory Mapping Wizard to add a Memory Map or Address Space to Your IP`
，這邊就直接 next next finish 按到底，中間選 AHB slave 即可。

做完之後，我們應該會在這個分頁下面有一個 entry，對他點右鍵 `Add Address Block`。

![add block](/images/xilinx/ahb_008_add_block.png)

預設會如下圖自動分配一個 4KB 的空間，對大多數的簡易 IP 控制界面來說，這個空間很夠用了
（對這個 IP 來說則是完全沒用，我們根本不管 Address）。  
我們就按下最後的 `Review and Package` 一路 yes 到底就完成 IP 打包。

![assigned](/images/xilinx/ahb_009_address_blocks.png)

# 連接 SoC

接著，我們回到 SoC 的頁面拉出下述三個方塊並且互相連接，由於前面有
[AXILite]({{< relref "PynqZ2_AXILite" >}})
講過怎麼做這些事情了，所以這邊只簡單條列要做的事情。

1. 把 CPU 開出一個 master port，例如說 `M_AXI_GP0`。
2. 新增 `AXI AHBLite Bridge` 跟我們新增的 AHB IP。
3. 使用 AXI Interconnect 把上述三者串連起來，路徑是 
    1. CPU M_AXI_GP0 - AXI Interconnect Slave S00_AXI
    2. AXI Interconnect Master M00_AXI - AXI AHBLite Bridge AXI4
    3. AXI AHBLite Bridge M_AHB - AHB IP AHB
4. 用自動連線功能把 clock, reset 全部連接起來。

最後，有一個比較細微的地方要手動處理。  
由於 Vivado 的提供的 AHB master 沒有 bus arbiter，不會自動連接 
slave 的 `HSEL` 與 master ready，Vivado 的檢查功能會在此刻回報有埠沒有接。

幸好，在 master 跟 slave 是一對一的情形下，我們可以透過 Constant Block 
把 slave `HSEL` 設定成 `1'b1`，並且把 
slave 的 `HREAYOUT` 接上 master 的 `HREADY`，如下圖所示：

![connect hready](/images/xilinx/ahb_012_connect_hready.png)

全部連接完成的接線如下圖所示：
![block diagram](/images/xilinx/ahb_010_block_diagram.png)

最後一步是點開 `Address Editor`，在 AHB port 上 assign 一塊 4K 的 memory 
assign 的 address 這個數字很重要可以記起來。

# 測試 bitstream

## Python Pynq

跟 AXI lite 不一樣，只要接了 AHB bus 的話，是沒辦法用 Python pynq 
來載入 .bitstream 檔的，會遇到以下的錯誤：
```txt
Expected design_1:AhbCli_0[block]:AHB[port] to be SubordinatePort when assigning base address
```
主要原因是 Python pynq 在剖析 .hwh 檔時，並不支援非 AXI 的埠，因此包括 AHB 和
[APB](https://discuss.pynq.io/t/error-when-loading-overlay-with-axi-to-apb-bridge/6814) 都是不能用的。  
就目前手邊資訊看來，Xilinx 沒有任何計劃想修正這個問題，如果要使用 Pynq 
就必須手動對系統內 hwh metadata parser 進行修改，如上述的 APB 討論中的解法。

## C Pynq

因為 python Pynq 不支援的關係，我們要改用其他人寫的 [C API](https://github.com/mesham/pynq_api)
，並用 mmap 的方式去存取 AHB bus 所在的區間：

以下是測試使用的 main.c，BASE_ADDR 要填入上面 Address Editor 中 Vivado
給出的位址，和上面 C API 中的 pynq_api.c 一起編譯為執行檔：
```c
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <stdint.h>

#include "pynq_api.h"

#define BASE_ADDR  0x43C00000
#define AHB_BASE_ADDR  0x43C10000
#define MEM_SIZE   0x1000   // 4 KB

int main(int argc, char *argv[]) {
  if (argc != 2) {
    fprintf(stderr, "Usage: *.bit\n");
    return 1;
  }

  char *bitstream_path = argv[1];

  printf("Creating overlay device from:\n");
  printf("  Bitstream: %s\n", bitstream_path);

  if (PYNQ_loadBitstream(bitstream_path) == PYNQ_ERROR) {
    fprintf(stderr, "Failed to load bitstream\n");
    return 1;
  }

  printf("  Bitstream loaded successfully\n");

  int fd;
  volatile uint32_t *map_base;

  // Open /dev/mem
  fd = open("/dev/mem", O_RDWR | O_SYNC);
  if (fd < 0) {
    perror("open");
    return 1;
  }

  // Map physical address to user space
  map_base = mmap(NULL, MEM_SIZE, PROT_READ | PROT_WRITE, 
                  MAP_SHARED, fd, BASE_ADDR);

  if (map_base == MAP_FAILED) {
    perror("mmap");
    close(fd);
    return 1;
  }

  printf("Write 0x%08X with 0x%08X\n", BASE_ADDR, map_base[0] = 0x5a5aa5a5);
  printf("Read 0x%08X get 0x%08X\n", BASE_ADDR + 512, map_base[0]);

  // Unmap and close
  munmap((void *)map_base, MEM_SIZE);
  close(fd);

  return 0;
}
```

編譯與執行的結果如下：
![AHB test with C](/images/xilinx/ahb_014_test.png)

# 結論

這篇文章說明如何在 IP 的介面上接上常見的 AHB bus，當然 Vivado 還提供了各種不同的 bus
在 `Interface Definition` 就有許多不同的選項可供選擇。  
這篇算是個打底，下一篇我們在連接 AXI Stream 上也需要做類似的事情。