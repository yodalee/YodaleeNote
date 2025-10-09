+++
author = "Yu-Sheng Lin"
title = "從一開始的 Xilinx SoC 開發，PetaLinux 使用（三）"
date = "2021-09-14"
description = "從一開始的 Xilinx SoC 開發，PetaLinux 使用（三）"
featured = false
tags = [
    "xilinx",
    "petalinux",
]
categories = [
    "tool",
    "technical",
]
series = ["從一開始的 Xilinx SoC 開發，PetaLinux 使用"]
aliases = []
math = false
+++

前面的系列中，我們設定好 PetaLinux 並編譯出一個能用來在 SD 卡上開機的檔案系統了。這篇文章中，我們將會寫出一份 C code 讓 PL side 的 DMA 動起來，在 PL/PS side 的 DDR 之間搬運資料。

<!--more-->

### SoC 設定回顧

回顧一下我們的兩個 interconnect 的 slaves 的 address 設定是這樣：

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

在這個 SoC 中，這篇文章將會說明如何從頭到尾進行以下操作：

1. 用 CPU 在 PS DRAM 寫入一些資料，方便起見叫 *PSMem1*。
1. 用 CPU 操作 DMA 控制界面，叫他把資料從 PS DRAM 搬到 PL DRAM (*PSMem1* → *PLMem1*)。
1. 用 CPU 操作 DMA 控制界面，叫他把資料從 PL DRAM 互相搬移 (*PLMem1* → *PLMem2*)。
1. 用 CPU 操作 DMA 控制界面，叫他把資料從 PL DRAM 搬回 PS DRAM (*PLMem2* → *PSMem2*)。
1. 用 CPU 在驗證 PS DRAM 的資料是否正確 (*PSMem2*)。

### 在 PS DRAM 中寫入資料

由於作業系統的緣故，在 PS DRAM 中寫入資料不是簡單的事情。例如說我們要把資料放在 DDR 中第 1.5GB 的位置好了，我們不能直接寫：

{{< highlight cpp >}}
unsigned *ptr = 0x60000000;
ptr[0] = 0;
{{< /highlight >}}

因為作業系統不可能讓你直接存取實際的記憶體位置，因此就算這個程式是用 root 來執行都無法達到我們要的效果。

幸好，Linux 提供一個簡便的方式可以讓我們繞過，也就是透過 `/dev/mem` 來存取 PS DRAM，甚至是 DMA 控制界面，透過 `open("/dev/mem")` 加上 `mmap` 的組合，我們還是可以拿到一個 pointer 來使用，雖然麻煩了許多。

{{< highlight cpp >}}
int fd = open("/dev/mem", O_RDWR | O_SYNC);
size_t desired_bytes = 1<<20; // 1MB
unsigned *volatile ptr = (unsigned*) mmap(
   0,
   desired_bytes,
   PROT_READ | PROT_WRITE,
   MAP_SHARED,
   fd,
   0x60000000 // 1.5GB
);
ptr[0] = 0;
{{< /highlight >}}

然而現在還有第二個問題，由於整個作業系統都是 Linux 管理的，就算我們寫入了想要的位置，說不定 Linux 已經把這塊記憶體分配給其他程式使用了。因此我們還需要保證 Linux 不會把這塊記憶體分配下去，這時候就是前面一篇文章中 `project-spec/meta-user/recipes-bsp/device-tree/files/system-user.dtsi` 派上用場的時候了。

在這個檔案裡面，本來有一個這樣的片段。

{{< highlight text >}}
/include/ "system-conf.dtsi"
/ {
   xlnk {
      compatible = "xlnx,xlnk-1.0";
   };
};
{{< /highlight >}}

加上這樣的一段描述，就可以讓 Linux 知道從 1.5GB (`0x60000000`) 開始的 64MB (`0x04000000`)，這塊記憶體是不能使用的。注意有時候這個位置會跟其他已經保留的位置衝突，有時候需要調整一下才不會衝突，但是我目前也不確定要怎麼樣才知道有沒有衝突......

{{< highlight text >}}
/include/ "system-conf.dtsi"
/ {
   xlnk {
      compatible = "xlnx,xlnk-1.0";
   };
   reserved-memory {
      #address-cells = <1>;
      #size-cells = <1>;
      ranges;
      reserved: buffer@0x60000000 {
         no-map;
         reg = <0x60000000 0x04000000>;
      };
   };
};
{{< /highlight >}}

接著再編譯一次 PetaLinux，把 `BOOT.BIN`、`image.ub`、`boos.scr` 重新複製到 SD 卡的第一個磁區。

{{< highlight text >}}
petalinux-build
cd images/linux/
petalinux-package --boot --fsbl zynqmp_fsbl.elf --fpga system.bit --pmufw pmufw.elf --atf bl31.elf --u-boot u-boot.elf --force
{{< /highlight >}}

### 操作 DMA

要操作位於 `0x80000000` 的 DMA，我們也只要對 DMA 的位置 `mmap` 出一塊空間。

{{< highlight cpp >}}
int fd = open("/dev/mem", O_RDWR | O_SYNC);
size_t desired_bytes = 64<<10; // 64KB
unsigned *volatile ptr = (unsigned*) mmap(
   0,
   desired_bytes,
   PROT_READ | PROT_WRITE,
   MAP_SHARED,
   fd,
   0x80000000
);
// Then do something to DMA by manipulating ptr
{{< /highlight >}}

然而問題來了，我們要怎麼對這個 pointer 操作，才能叫 CDMA 做事呢？我們在 [官方論壇](https://forums.xilinx.com/t5/Design-and-Debug-Techniques-Blog/AXI-CDMA-Linux-user-space-example-on-Zynq-UltraScale-RFSoC/ba-p/1096735) 上找到了答案，我把他稍微修改了一下，包裝成一個函數。詳細內容就不要深究了，總之就是照著標準對 CDMA 的 register 進行操作。

{{< highlight cpp >}}
#define XAXICDMA_CR_OFFSET      0x00000000  /* Control register */
#define XAXICDMA_SR_OFFSET      0x00000004  /* Status register */
#define XAXICDMA_SRCADDR_OFFSET 0x00000018  /* Source address register */
#define XAXICDMA_DSTADDR_OFFSET 0x00000020  /* Destination address register */
#define XAXICDMA_BTT_OFFSET     0x00000028  /* Bytes to transfer */

unsigned int dma_set(unsigned* dma_virtual_address, int offset, unsigned int value)
{
   dma_virtual_address[offset>>2] = value;
}

unsigned int dma_get(unsigned* dma_virtual_address, int offset)
{
   return dma_virtual_address[offset>>2];
}

void dma_memcpy(unsigned* volatile vadd_cdma, off_t src, off_t dst, size_t nbyte)
{
   unsigned reg = dma_get(vadd_cdma, XAXICDMA_CR_OFFSET);
   unsigned status = dma_get(vadd_cdma, XAXICDMA_SR_OFFSET);
   dma_set(vadd_cdma, XAXICDMA_CR_OFFSET, XAXICDMA_XR_IRQ_SIMPLE_ALL_MASK);
   reg = dma_get(vadd_cdma, XAXICDMA_CR_OFFSET);
   status = dma_get(vadd_cdma, XAXICDMA_SR_OFFSET);
   dma_set(vadd_cdma, XAXICDMA_SRCADDR_OFFSET, src);
   reg = dma_get(vadd_cdma, XAXICDMA_SRCADDR_OFFSET);
   status = dma_get(vadd_cdma, XAXICDMA_SR_OFFSET);
   dma_set(vadd_cdma, XAXICDMA_DSTADDR_OFFSET, dst);
   reg = dma_get(vadd_cdma, XAXICDMA_DSTADDR_OFFSET);
   status = dma_get(vadd_cdma, XAXICDMA_SR_OFFSET);
   dma_set(vadd_cdma, XAXICDMA_BTT_OFFSET, nbyte);
   while(1) {
      status = dma_get(vadd_cdma, XAXICDMA_SR_OFFSET);
      if(status & (1 << 12)) {
         printf("DMA transfer is completed \n");
         break;
      }
   }
   reg = dma_get(vadd_cdma, XAXICDMA_BTT_OFFSET);
   status = dma_get(vadd_cdma, XAXICDMA_SR_OFFSET);
}
{{< /highlight >}}

接著，我們用這個 function 去建構我們的測試，先把 PSMem1 初始化，依序搬到 PLMem1、PLMem2、PSMem2，最後檢查 PSMem2 的內容是不是跟 PSMem1 一樣：

{{< highlight cpp >}}
off_t PS = 0x060000000ll;
off_t PL = 0x100000000ll;
size_t SIZE = 1<<10;
// Initialize PSMem1 using mmap'ed pointer
for (int i = 0; i < SIZE/sizeof(unsigned); ++i) {
   ptr_ps[i] = i;
}
// Copy from PSMem1 -> PLMem1 -> PLMem2 -> PSMem2
dma_memcpy(ptr_cdma, PS     , PL     , SIZE);
dma_memcpy(ptr_cdma, PL     , PL+SIZE, SIZE);
dma_memcpy(ptr_cdma, PL+SIZE, PS+SIZE, SIZE);
// Check PSMem2 using mmap'ed pointer
for (int i = 0; i < SIZE/sizeof(unsigned); ++i) {
   assert(ptr_ps[i+SIZE] == i);
}
{{< /highlight >}}

如果之前 rootfs 上面有安裝 gcc 的話，完成這個程式之後，把他放到 SD 卡上面的隨便一個位置上面開機，接著跟一般的 Linux 一樣 gcc 編譯就好了。

{{< highlight cpp >}}
gcc main.c -o dma_test
./dma_test
{{< /highlight >}}

如果 assertion 有通過的話，這樣應該就是有完成測試了。

### 結論

這篇文章用了最簡單粗暴的方式，把 `/dev/mem` 打開，然而其實一般來說不應該使用這麼 hacky 的界面，而應該用 Linux kernel 裡面現有的 driver 去達成。下一篇文章中，我將會說明如何寫一個 Linux kernel driver，取代掉 `dma_memcpy` 這麼 hacky 的作法。
