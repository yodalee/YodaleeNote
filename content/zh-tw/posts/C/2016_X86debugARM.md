---
title: "在X86機器上debug ARM 執行檔"
date: 2016-05-13
categories:
- embedded system
tags:
- embedded system
- arm
- archlinux
series: null
---

以後有可能會用到，寫這篇純粹做個記錄。  

故事是這樣子的，最近閒來無事研究一下傳說中 jserv 大神的amacc，有些地方實在看不出程式執行至此時一些變數的值為何，這時我們就要用gdb 了  
不過amacc 是用 arm-linux-gnueabihf-gcc 編出來的arm 執行檔，我們host gdb 是X86 在執行時就會報錯：可執行檔格式錯誤  
如果用arm-linux-gnueabihf-gdb 呢：它會寫 Don't know how to run.  
<!--more-->

我們需要用到server-client 的架構，server 端在實體target 上可以用 gdbserver，這會需要對gdb-server, gdb 特別編譯；
gdb configure target 為arm-linux-gnueabi，gdbserver configure host 為arm-linux-gnueabi。  
如這篇所述：  
<https://sourceware.org/gdb/wiki/BuildingCrossGDBandGDBserver>  

我們可以用qemu 的 debug 來代替gdbserver：  
首先執行qemu ，指定debug 的port 為9453：  
qemu-arm -L /usr/arm-linux-gnueabihf -g 9453 amacc tests/shift.c  

在另外一個終端機，打開arm-linux-gnueabihf-gdb，這是已經configure target為arm-linux-gnueabi 的gdb：  
arm-linux-gnueabihf-gdb ./amacc tests/shift.c  

在gdb 裡面連接remote target：  
target remote localhost:9453  

再來就能用c 開始跑了，happy debug。  

相關參考：  
<http://kezeodsnx.pixnet.net/blog/post/31901130-gdbserver-remote-debug-%E6%B8%AC%E8%A9%A6>  
