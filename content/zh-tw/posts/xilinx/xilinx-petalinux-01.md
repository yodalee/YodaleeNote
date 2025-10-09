+++
author = "Yu-Sheng Lin"
title = "從一開始的 Xilinx SoC 開發，PetaLinux 使用（一）"
date = "2021-08-25"
description = "從一開始的 Xilinx SoC 開發，PetaLinux 使用（一）"
featured = true
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

在前系列的文章中，我們完成了基本的 Vivado SoC 建立流程，SoC 上面具有 CPU 以及 PL side 的 DMA 跟 DDR 控制器。最後，我們生成了一個 xsa 檔案，包含了這個 SoC 的所有必要資訊。接下來的流程中，將使用 PetaLinux，從 xsa 檔案產生出 Linux image、file system 等等資訊。另外，由於這系列有點長，所以就把系列標題改成「從一開始的 Xilinx SoC 開發了」。

<!--more-->

### 安裝 PetaLinux ...的預備工作

PetaLinux 的安裝相當囉唆，主要歸功於下面幾個理由：

* 官方支援的作業系統相對老舊，如在 2021 時支援 Ubuntu 18.04, CentOS 6 等。
* 官方支援 bash 以及 csh，考慮到 csh 很難用，基本上就是用 bash。
* 安裝的時候只能用 non-root user。
* 安裝的 dependency 很多，而且很容易安裝到一半才跳出說少了什麼 dependency。

對於 ArchLinux 或是新一點的 Ubuntu 用戶，這些限制都很容易出問題。因此，特別開了一個章節來講怎麼安裝 PetaLinux。首先，我們用自己的帳號當 user 開一個 docker 叫做 petalinux，並把 PetaLinux 相關的資料都放在 `${HOME}/PetaLinux` 下。

{{< highlight bash >}}
cd
mkdir PetaLinux
docker run -u `id -u`:`id -g` --name petalinux_${USER} -e HOME=/workspace -w /workspace \
           -v ${HOME}/PetaLinux:/workspace -it ubuntu:18.04 /bin/bash
{{< /highlight >}}

接著按 `ctrl+d` 登出，因為沒有 root 我們不好安裝東西。在 container 中，用 root 登入安裝以下 package。

{{< highlight bash >}}
docker start petalinux_${USER}
docker exec -u 0:0 -it petalinux_${USER} /bin/bash
dpkg --add-architecture i386
apt update
apt upgrade
apt install gawk vim gcc xterm autoconf libtool texinfo zlib1g-dev \
    zlib1g-dev:i386 gcc-multilib build-essential libncurses5-dev \
    net-tools python rsync less locales cpio tmux
vim /etc/locale.gen
locale-gen
{{< /highlight >}}

**重點：** 其中 vim 那一行請找到 `en_US.UTF-8 UTF-8`，把開頭的井字刪掉。

#### 可能要提昇 inotify 的數量

似乎在某些新的 Linux distro 開出來的 docker 下面，作者有遇過這樣的 error (Ubuntu 22.04/ArchLinux)。

{{< highlight text >}}
ERROR: Fail to add user layer: /workspace/run/project-spec/meta-user.
ERROR: Fail to config project.
{{< /highlight >}}

查看 log 之後，發現是 inotify 導致的 error，可以在 **docker 外面** 提昇 inotify 的上限。至於為何不是每個 Linux distro 都有同樣的問題，目前原因不明。

{{< highlight bash >}}
sudo sysctl fs.inotify.max_user_instances=1024
{{< /highlight >}}

### 安裝 PetaLinux
接著我們把 **xsa 檔案跟 PetaLinux 安裝檔**都丟到 `/home/PetaLinux` 下面，此外我們還需要 **bsp 檔案**，這個檔案是 example 或是設計廠會提供的。下面的例子中，我的安裝檔名叫做 `petalinux-v2020.2-final-installer.run`，如果前面的 dependency 沒問題，安裝步驟倒是相當容易，一路 yes 到底就可以了，中途也會冒出幾個可以忽視的 warning。

{{< highlight bash >}}
docker start petalinux
docker attach petalinux
cd /workspace
./petalinux-v2020.2-final-installer.run -d /workspace/install
{{< /highlight >}}

安裝好 PetaLinux 之後，用 `petalinux-create` 來初始化 PetaLinux project。接著我們就可以 `cd` 到這個 project 裡面。

{{< highlight bash >}}
source /workspace/install/settings.sh
petalinux-create -t project -s XXX.bsp -n my_awesome_project_name
cd my_awesome_project_name
petalinux-config --get-hw-description=XXX.xsa
{{< /highlight >}}

最後，我們用這個指令編譯出開機 FPGA 上的 Linux 需要的所有檔案，這個指令要跑一陣子，需要有點耐心。

{{< highlight bash >}}
petalinux-build
{{< /highlight >}}

### 結論

本文的最後中，在 `petalinux-config` 裡面有許多設定要調整，而且關於 `petalinux-build` 編譯出來的檔案要如何使用也都沒有說明，就留在下一篇文章說明吧。
