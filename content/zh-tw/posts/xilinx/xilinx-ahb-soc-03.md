+++
author = "Yu-Sheng Lin"
title = "在 Xilinx SoC 上放上自己的 IP（三）"
date = "2022-05-25"
description = "在 Xilinx SoC 上放上自己的 IP（三）"
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

上一篇系列文中，我們把自己寫的 Verilog AHB IP 包裝成 Xilinx FPGA 的 SoC，並且編譯了一個 bitstream 出來，接下必須要將 bitstream 燒錄到 FPGA 上，在 FPGA 執行 PetaLinux 系統，寫一個 C++ 程式去控制這個 Verilog AHB IP。

<!--more-->

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
