---
title: "使用 docker 在 ubuntu 上面執行 EDA 軟體"
date: 2025-04-04
categories:
- Setup Guide
tags:
- Synopsys
- EDA
- docker
- Ubuntu
series: null
---

故事是這個樣子的，說到 Linux 作業系統，現下市佔率最高的當然是 Ubuntu 了，無論從體驗、安裝的難易度、
參考文件、社群支援、更新穩定性來看，ubuntu 都是 Linux 的首選。  
但是如果你是做硬體的，上面這段話就不適用了，由於商用作業系統的支援，大多數的 EDA 軟體選擇的都是 RedHat 系列的，
包括 RedHat Enterprise Linux (RHEL) 或是開源版本的 CentOS。
<!--more-->

過去我們很常做的，就是買台新的主機，在上面只灌 CentOS 與 EDA 軟體連線使用，白白浪費了一台主機。  
時至今日，我們有個更簡單的解決方案：透過 Docker 直接在 Ubuntu 環境中建立一個支援的作業系統的容器，
就能使用它的執行環境來執行**放在 Ubuntu 電腦中**的 EDA 軟體。
這樣就能避掉 EDA 軟體在 Ubuntu 上支援不佳的問題，又能保有日常使用 Ubuntu 的可能性，不用白白犧牲一台電腦。

這篇文章就是個人完成這些步驟的流程記錄，讓你在 Ubuntu 上無痛啟動 RockyLinux 執行 EDA 工具。

# 為什麼不用 Ubuntu 執行 EDA？
目前我的經驗只試過兩個：Synopsys VCS 跟 Synopsys Design Compiler，在 Ubuntu 上安裝，大概可以分成兩點：  
1. 套件支援：有些 EDA 軟體依賴的函式庫，因為 Ubutnu apt 和 RHEL yum 的套件管理系統不同，在 Ubuntu 上安裝需要費一番工夫去找到正確的套件。
2. 動態函式庫相容性，相比上一項這項更麻煩，Synopsys Design Compiler 需要的 glibc 是 RHEL 特別的版本，
和 Ubuntu 較新的不相容，執行時會遇上 GLIBC_PRIVATE 的錯誤：

> /lib/x86_64-linux-gnu/libpthread.so.0: version `GLIBC_PRIVATE' not found

第一點只是麻煩，下面會看到就算是 RHEL 也要自己慢慢用 yum, dnf 去找套件，沒差太多。  
第二點真的就是硬傷，網路上[唯一找到的解法](https://bbs.eetop.cn/forum.php?mod=viewthread&tid=971027)，
是自行編譯並安裝 glibc 2.31 版，再使用 patchelf 更改執行檔的 rpath，讓它改用 glibc 2.31 的 ld-linux 及動態函式庫。  
不是無解，但這個解也太複雜太折騰人了。  

# 使用 Docker 執行 Rocky Linux

目前 EDA 軟體推薦的作業系統有下面幾個：
* RHEL 8.4 以上
* CentOS 7 以上
* Rocky Linux

由於 CentOS 8 在 2021 年底停止維護，RedHat 推動 CentOS Stream 作為滾動更新版，
這與傳統的穩定版本 CentOS 7 存在較大差異，因此這次選用 CentOS 8 停止維護後誕生的 Rocky Linux 作為安裝對象。

EDA 軟體直接安裝在 Ubuntu 內即可，我鄙擇的安裝路徑是 `/eda`，之後我們再把 /eda 掛進 Rocky Linux 內。

至於 Docker 安裝步驟，這種現在都問 ChatGPT 就好了，以下是提問：

> 請就你所知道步驟，整理如何在 ubuntu 上使用 Docker 安裝 RockyLinux 執行環境。

## 一：安裝 Docker
如果你的 Ubuntu 還沒有安裝 Docker，可以執行以下指令來安裝：
```bash
sudo apt update
sudo apt install -y docker.io
sudo systemctl enable --now docker
sudo usermod -aG docker $USER  # 讓當前使用者不需要 sudo 就能執行 docker
newgrp docker  # 立即生效
```
確認安裝成功：
```bash
docker --version
```

## 二：建立 Dockerfile：RockyLinux + EDA 套件環境

在 Ubuntu 上建立一個資料夾，例如 `~/eda_docker`，然後建立 `Dockerfile`：

```Dockerfile
# ~/eda_docker/Dockerfile
FROM rockylinux:9

# 安裝必要套件（32-bit support, GUI, 開發工具組）
RUN dnf update -y && \
    dnf install -y \
        xorg-x11-xauth xauth xterm \
        epel-release wget vim tar time csh ksh \
        graphite2 bc \
        iputils telnet \
        gcc gcc-c++ \
        glibc.i686 libstdc++.i686 elfutils-libelf.i686 \
        libXrandr libGL libXcomposite \
        libnsl linsl.i686 pulseaudio-libs-devl \
        libXi libXp libXp.i686 libXt libXt.i686 \
        libX11.i686 libXext.i686 libXrender.i686 libXtst.i686 && \
    dnf install -y lsb_release && \
    dnf clean all

# 建立 /usr/eda symlink 指向 /eda（host 目錄）
RUN ln -s /eda /usr/eda
```

大致說明一下，這邊看到這排是安裝 vcs 與 design compiler 後，在執行時發現必須安裝的執行檔與函式庫。  
其中 [pulseaudio-libs-devel](https://blog.csdn.net/zhang197093/article/details/106804900) 
顯示需要的函式褲為 libpulse-mainloop-glib.so.0，費了一番工夫才找到這個函式庫。

---

## 三、建構 Docker 映像檔

在 `~/eda_docker` 資料夾中執行：

```bash
cd ~/eda_docker
docker build -t eda_image .
```

## 四、執行 RockyLinux 容器

執行前，開放本地 X11 給容器：

```bash
xhost +local:docker
```

然後執行容器：

```bash
docker run -it --rm \
    --name eda_container \
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v /eda:/eda \
    -v /etc/hosts:/etc/hosts:ro \
    eda_image /bin/tcsh
```

# 執行

ChatGPT 提供的回答，基本上都沒什麼問題，照做即可，以下是一些額外的除錯與設定：

## udev_monitor_receive_device realloc crash

design compiler 在虛擬機內執行，會導致 libudev 呼叫 realloc 時 crash，相關的錯誤訊息可以找到的參考資料包括：
* [Systemd 在虛擬機執行的討論](https://github.com/systemd/systemd/issues/19733)
* [Quartus in Docker](https://www.jamieiles.com/posts/quartus-docker/)
* [Quartus in WSL](https://community.intel.com/t5/Intel-FPGA-Software-Installation/Running-Quartus-Prime-Standard-on-WSL-crashes-in-libudev-so/m-p/1189032)

參照 systemd 的相關討論，目前有兩個解法
1. 在執行前設定 LD_PRELOAD=/lib64/libudev.so.1
2. 設定使用 read-only mode 掛載 /sys

兩個我試過都能解決問題，目前我是使用第二種，請見下面的 eda.sh。

## eda.sh

另外為了簡化工作流程，可以另外寫一個 eda.sh 執行 docker 指令。
```bash
# eda.sh
# license setting in host /etc/hosts/
# -v /sys:/sys:ro required by design compiler, otherwise udev will crash
xhost +local:
docker run -it --rm \
  --name eda_container \
  -e DISPLAY=$DISPLAY \
  -v /etc/hosts:/etc/hosts:ro \
  -v /sys:/sys:ro \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v $HOME/eda_files:/mnt/eda \
  -v /eda:/eda \
  eda_image /bin/tcsh
```

# 結論

我們使用 docker 在 Ubuntu 內安裝 Rocky Linux，並使用 Rocky Linux 來執行 Synopsys 的 VCS 與 Design Compiler。  
目前的測試情況，VCS 能正確生成 simv 檔並進行模擬；Design Compiler 則可以打開圖形介面與 dc_shell，還沒實際合成。  
如果真的有需要，再來看看能不能執行更多工具如 INNOVUS, Verdi 等，如果有測試過再更新在這裡。