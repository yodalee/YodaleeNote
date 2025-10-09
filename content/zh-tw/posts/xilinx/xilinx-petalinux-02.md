+++
author = "Yu-Sheng Lin"
title = "從一開始的 Xilinx SoC 開發，PetaLinux 使用（二）"
date = "2021-09-01"
description = "從一開始的 Xilinx SoC 開發，PetaLinux 使用（二）"
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

上一篇文章中，我們透過 `petalinux-build` 編譯完了某些東西，這些東西可以讓我們製作一個可以開機的 SD 卡，讓 Xilinx 的 SoC 可以開機，並且可以跟 FPGA 端互動。

<!--more-->

### 製作 SD 卡分割表
首先，為了讓 PetaLinux build 出來的東西可以放到 SD 卡執行，我們要先把 SD 卡分割成以下的樣子：

* FAT16 分割區，200MB 一定足夠。
* 剩下都做成 ext4 分割區。

### PetaLinux 資料夾結構

接著，我們來看一下 PetaLinux workspace 中一些比較重要的資料夾，這些資料夾中，可能包含了一些檔案，要複製到 SD 卡上，或是這些檔案會影響到我們編譯出來的東西。

* `components/plnx_workspace/device-tree/device-tree/`
	* 不能亂改這個資料夾裡面的內容，但是裡面的 `system-conf.dtsi`、`system-conf.dtsi`、`pl.dtsi` 是在描述整個 SoC，可以簡單翻一下。
* `images/linux/`
	* 許多編譯出來的檔案都在這邊，包括要放在 SD 卡的開機磁區跟根目錄磁區的檔案都在這邊。
* `project-spec/meta-user/recipes-bsp/device-tree/files/`
	* 前面描述整個 SoC 的檔案是不能更動的，如果要微調 SoC 的描述的話，只能在這個資料夾下面的 `system-user.dtsi` 去作調整。順帶一提，裡面還有一個 `pl-custom.dtsi`，看起來也像提供調整 SoC 的功能，但是預設是不使用這個檔案的，非常的整人。

### 重新編譯 PetaLinux

如果是照著上一篇的步驟編譯的話，全部用的是預設的設定編譯的，而預設的設定可能不是用 SD 卡開機，因此可能會開不了機。為此，我們需要正確設定之後重新編譯一次，透過這個指令重新設定 PetaLinux。

{{< highlight bash >}}
petalinux-config
{{< /highlight >}}

下了這個指令，我們會看到這樣的界面。

<img src="/post_images/xilinx-petalinux/000-petalinux-config.png" width="500" class="default-insert" />

這邊條列出要更動的設定：

* *Subsystem AUTO Hardware Settings*
	* *Memory Settings*
		* *System memory size* 這邊設定成 PS side 總 memory 的一半，最多 2GB。
	* *Advanced bootable images storage Settings*
		* *boot image settings* 的 *image storage media* 是 primary sd。
		* *u-boot env partition settings* 的 *image storage media* 是 primary sd。
		* *kernel image settings* 的 *image storage media* 是 primary sd。
* *FPGA Manager*
	* *Fpga Manager* 確定有關掉。
* *Image Packaging Configuration*
	* *Root filesystem type* 選 ext4，跟我們上面的設定一樣。
	* *Device node of SD device*，是 ext4 那個磁區 `/dev/mmcblk0p2`。
	* *Root filesystem formats* 留下 cpio 就好，不動也是可以。
	* *Copy final images to tftpboot* 可以關掉。
* *Yocto Settings*
	* *Parallel thread execution* 可以設定最多用幾個 thread 去跑。

最後，我們用這個指令編譯出開機 FPGA 上的 Linux 需要的所有檔案，這個指令還是要跑一陣子，需要有點耐心。

{{< highlight text >}}
petalinux-build
cd images/linux/
petalinux-package --boot --fsbl zynqmp_fsbl.elf --fpga system.bit --pmufw pmufw.elf --atf bl31.elf --u-boot u-boot.elf --force
{{< /highlight >}}

### 安裝到 SD 卡

上一個步驟中，我們 `cd` 到了 `images/linux/` 資料夾下應該會有這四個檔案 `BOOT.BIN`、`image.ub`、`boos.scr`、`rootfs.cpio`，這四個檔案可以幫助我們建構開機用的 SD 卡。

* 第一個磁區
    * 把 `BOOT.BIN`、`image.ub`、`boos.scr` 複製進來就好。
* 第二個磁區
    * （這個指令可以先不要跑，等下一段看完之後再跑。）
    * `cd` 到第二個磁區執行 `cpio -i < /XXX/XXX/rootfs.cpio`，注意中間有個 `<`，那不是筆誤，這個指令會把檔案系統 (rootfs) 解開在當前的資料夾。
    * 這個指令只有更動 rootfs 的時候要跑，大部分的時候 `petalinux-build` 之後不用跑。

### Rootfs

經過上述步驟，已經可以把 SD 卡插入 FPGA 開機了，FPGA 上有一些開關要撥到正確的位置才能開機，關於這點請遵循原廠教學。不過預設的檔案系統安裝的東西很少，如果我們希望上面有更多軟體的話，還須額外設定 rootfs。

Rootfs 其實就是一個檔案，可以想像他是一種 tar，只不過是專門給 Linux 檔案系統用的 tar，可以打包完整的 Linux root filesystem，所以才叫做 rootfs，而 cpio 也是 rootfs 的格式之一。

我們可以透過 `petalinux-config -c rootfs` 來選取說我們希望要在這個 Linux 上有安裝哪些軟體，操作方式跟一般 Linux 安裝軟體差不多，就是把想要的檔案勾起來就好了。因為不會想要每次都編譯、解開 rootfs，所以這個步驟建議是把需要的檔案一次勾選完。這邊我只列了我覺得最少的必要軟體，一般 linux 常見的 sudo, vim, python...，就要依據需求自己裝了。

* *Filesystem Packages*
	* *base*
		* *tar* 嗯.....就是解壓縮用的，很重要。
	* *misc*
		* *packagegroup-core-buildessential* 就是 ubuntu 的 build-essential，像 gcc 什麼的都包在這包了。
* *Image Features*
	* *ssh-server-dropbear* 關掉
	* *ssh-server-openssh* 打開，雖然 dropbear 是比較精簡的 ssh server，但是因為 openssh 用習慣了，所以還是選他吧。
* *PetaLinux RootFS Settings*
	* 可以改 root 密碼

設定完成之後，一樣執行 `petalinux-build` （因為要編譯這些軟體，所以也是要很久），然後照[上面的步驟](\#安裝到-sd-卡)，把 cpio 解開到 SD 卡的 ext4 磁區上面就好了。最後，去依照 Linux 一般的 [openssh 設定流程](https://wiki.archlinux.org/title/OpenSSH)，設定一下 ssh 的連線方式，在 FPGA 開機之後，就可以用 ssh 登入了。

### 結論

這篇文章中，我們已經可以把 SD 卡插入 FPGA 開機了。下一篇文章吧我們終於要回到 FPGA 上，讓 PL side 的 DMA 動起來搬運資料。
