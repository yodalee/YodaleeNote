+++
author = "Yu-Sheng Lin"
title = "Vivado 安裝在 Linux 上的各種雷"
date = "2021-07-19"
description = "Vivado 安裝在 Linux 上的各種雷"
featured = false
tags = [
    "xilinx",
]
categories = [
    "tool",
    "technical",
]
series = []
aliases = []
math = false
+++

本篇文章紀錄了 Linux 上安裝 Vivado/Vitis/Vitis HLS/PetaLinux 2020.2 時，遇到過的問題們。

<!--more-->

### 問題一
#### 可能的現象
Vitis 在 create platform project 的時候，跑了很久什麼都沒跑出來，而且也沒佔用 CPU 資源，或許還會跳個錯誤訊息：

{{< highlight text >}}
xsct server communication channel is not established
{{< /highlight >}}

#### 可能的解法

單獨執行 Vivado 的 `xsct` 程式，發現這個錯誤：

{{< highlight text >}}
which: no xlsclients in (/usr/local/sbin:/usr/local/bin:...)
ERROR: xlsclients is not available on the system, please make sure xlsclients is available on the system.
{{< /highlight >}}

合理推論，我們沒有 `xlsclients` 這個程式，安裝即可解決。ArchLinux 的話，應該是 `extra/xorg-xlsclients` 套件。

對我並沒有用的解法們：
* [沒有用的解法一](https://www.xilinx.com/support/answers/69263.html)
* [沒有用的解法二](https://forums.xilinx.com/t5/Embedded-Development-Tools/Reason-xsct-server-communication-channel-is-not-established/td-p/868723)

### 問題二
#### 可能的現象
Vitis HLS 打不開：

{{< highlight text >}}
@E cannot exec arch command, error: couldn't execute "arch": no such file or directory
{{< /highlight >}}

#### 可能的解法

這個 error message 其實不是主要問題，[這篇文章](https://forums.xilinx.com/t5/Design-Entry/Vitis-HLS-2020-2-not-starting-only-splash-screen-visible/td-p/1187946) 提到的才是最大的問題，而且或許是特定版本的 2020.2 才有的問題。

在 `Vitis_HLS/2020.2/common/scripts/autopilot_init.tcl` 下，有一行加密過的 tcl。

{{< highlight text >}}
----%r&-'%rl%&n$&lt'v-=
{{< /highlight >}}

官方打錯了，最後一個字應該要是 `>` 才對。

另外 `couldn't execute "arch"` 也是可以解決的，只要建立一個 executable script 叫做 `arch`，放在 `$PATH` 下就好，他的功能跟 `uname -m` 一樣。

{{< highlight bash >}}
#!/bin/sh
uname -m
{{< /highlight >}}

有用的解法們：
* [有用的解法們一](https://aur.archlinux.org/packages/vivado)

### PetaLinux
在本文撰寫的時間，PetaLinux 支援之 Ubuntu 系作業系統為 16.04 & 18.04，雖然在 ArchLinux/Ubuntu 都能正常安裝，但是在 ArchLinux 下無法正確執行，Ubuntu 20.04 可以正確執行，但是會有警告。一個好的解決方法就是用 docker 安裝 Ubuntu 18.04，可以把 PetaLinux 的安裝資料夾 mount 上去，不需要在 docker 裡面安裝 PetaLinux。
