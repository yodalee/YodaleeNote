+++
author = "Yu-Sheng Lin, Yodalee"
title = "在 Xilinx SoC 上放上自己的 IP"
date = "2021-09-11"
description = "在 Xilinx SoC 上放上自己的 IP"
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

### 完成 IP

這個步驟做完之後，本來 `Ports and Interfaces` 的頁面應該會變得很乾淨：

<img src="/post_images/xilinx-ahb/006-mapped-port.png" width="400" class="default-insert" />

注意有的時候，clock 跟 reset 兩個信號線不一定會被自動辨認。在這個情形下，我們必須自行用同樣的方法，新增 `clock_rtl` 跟 `reset_rtl` 兩個 slave，然後把 port map 上去。

最後，我們把 AHB slave 跟 reset 都右鍵 `Associate Clocks`，告訴 Vivado 說這些信號是對齊 clock signal 的，這樣我們就**快**完成了（嗯對，還沒完成）。

<img src="/post_images/xilinx-ahb/007-associate-clock.png" width="300" class="default-insert" />

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

### 預先設定

這篇文章希望說明在 PetaLinux 上面編譯我們自己的 C++ 程式來操作自己寫的 Verilog IP，所以仍然必須編譯出 PetaLinux 在 FPGA 上執行起來。[前面的系列](series/在-xilinx-soc-上放上自己的-ip/) 的前兩篇中，提及了怎麼編譯出可用的 PetaLinux。

### 使用 UIO 讓 PetaLinux 開機之後可以看到我們的 IP

如果依照上面的文章步驟完成，理論上我們應該完成了這三件事（如果沒有的話，那請再回去確認一次）：

1. `petalinux-build` 完成了。
1. 在開機磁區放入了 `BOOT.BIN`、`image.ub`、`boos.scr` 三個檔案。
1. 在另外一個磁區用 `cpio` 解開了 rootfs。

接下來的步驟就是......前兩個步驟要修正一下重新跑一次。這是因為我們要透過 UIO 這個通用 driver 來把 Verilog IP 界面 expose 出來。UIO 這個 IP 相當好用，他可以：

1. 建立一個檔案，把給定 IP 的 AXI 的 register space 建立一個檔案，讓使用者可以透過 `mmap` 來 access。（這個功能雖然用 `/dev/mem` 也能作到，但是 UIO 的方法封裝程度相對高很多。）
1. 承上，這個檔案還允許我們很容易的去 wait IP 發出來的 interrupt。（`/dev/mem` 不行）

#### 修改 PetaLinux 開機參數

首先，我們要設定 PetaLinux 開機參數，讓其開機時可以 load UIO module，我們要去看 PetaLinux project 資料夾下面的 `components/plnx_workspace/device-tree/device-tree` 這個檔案，在我的設定中，我看到的參數是這樣。
{{< highlight text >}}
/ {
    chosen {
        bootargs = " earlycon console=ttyPS0,115200 clk_ignore_unused root=/dev/mmcblk0p2 rw rootwait";
    };
};
{{< /highlight >}}
接著，我們要修改 `project-spec/meta-user/recipes-bsp/device-tree/files/system-user.dtsi` 這個檔案，把剛剛的內容複製過去，並且後面加上一小段：
{{< highlight text >}}
/ {
    chosen {
        bootargs = " earlycon console=ttyPS0,115200 clk_ignore_unused root=/dev/mmcblk0p2 rw rootwait uio_pdrv_genirq.of_id=generic-uio";
    };
};
{{< /highlight >}}
（可能有人會想問，為什麼不直接覆蓋第一個檔案就好了呢？答案是，我也很想問這個很蠢的設計，總之第一個檔案是會在每次 `petalinux-build` 的時候覆蓋掉的，改他沒有用。）

#### 告訴 PetaLinux 我們的 Verilog IP 可以用 UIO 讀寫

在上一篇文章中，我們的 IP 在 SoC 裡面長這個樣子，可以看到他的名字是 `my_test_0`：

<img src="/post_images/xilinx-ahb/014-connect-hready.png" width="550" class="default-insert" />

所以我們同樣在 `project-spec/meta-user/recipes-bsp/device-tree/files/system-user.dtsi` 加入這段：
{{< highlight text >}}
&my_test_0 {
    compatible = "generic-uio";
};
{{< /highlight >}}
（為了保險起見，建議確認一下 `components/plnx_workspace/device-tree/device-tree/pl.dtsi` 裡面有沒有 `my_test_0` 這個字串。）

都完成了之後，最終的 `system-user.dtsi` 的前面幾行應該是長這個樣子：
{{< highlight text >}}
/include/ "system-conf.dtsi"
/ {
    xlnk {
        compatible = "xlnx,xlnk-1.0";
    };
    chosen {
        bootargs = " earlycon console=ttyPS0,115200 clk_ignore_unused root=/dev/mmcblk0p2 rw rootwait uio_pdrv_genirq.of_id=generic-uio";
    };
};
&my_test_0 {
    compatible = "generic-uio";
};
{{< /highlight >}}

接著，我們重複這兩個步驟就可以開機我們的 FPGA 了：

1. `petalinux-build`。
1. 在開機磁區放入 `BOOT.BIN`、`image.ub`、`boos.scr` 三個檔案。

### 撰寫操控 Verilog IP 的 C++ Code

接著，我們把 FPGA 開機，用 `cat` 可以找出我們的 UIO 在 OS 下對應到了哪個檔案：

{{< highlight bash >}}
cat /sys/class/uio/uio?/name
axi-pmon
my_test
axi-pmon
axi-pmon
...
{{< /highlight >}}
從上到下是 `/dev/uio0`、`/dev/uio1`、`/dev/uio2`...，像是這個例子就是 `/dev/uio1`。要讀寫 register，就直接用跟 [這篇](/2021/09/xilinx-petalinux-03/#%E5%9C%A8-ps-dram-%E4%B8%AD%E5%AF%AB%E5%85%A5%E8%B3%87%E6%96%99) 一樣的方法，去 `mmap` 就好了。這個 example 中，我們設計是不管怎麼讀取，都會得到 32 bit 的 `0x55665566`。

如果要等 interrupt 的話，則是連 `mmap` 都不需要，直接對 開出來的 file descriptor `write` 跟 `read` 各一次就好了。
{{< highlight cpp >}}
int ret;
write(fd, &ret, 4);
read(fd, &ret, 4);
{{< /highlight >}}

### 結論

這篇文章說明了怎麼把我們寫的 IP 透過 UIO 拉出來，UIO 提供了一個免寫 driver 的方式來操控 IP，對於僅需要簡單 register, interrupt 控制的 IP 來說相當便利。
