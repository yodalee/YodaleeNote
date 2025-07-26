---
title: "用 verilator 輔助數位電路設計：後記"
date: 2023-09-10
categories:
- verilog
tags:
- verilog
- verilator
series:
- verilator
forkme: rsa256
images:
- /images/verilator/RSAcontributor.png
---

這次開發 RSA 256 ，整體來說我覺得比 2010 年那時候順多了。  
2010 年因為第一次接觸 verilog 和 FPGA，在兩個月內要衝出 RSA 256，自然也不會懂什麼 valid/ready，
現在回去看介面都是用 start 配 ready，相當於只有 i_valid 跟 o_valid，除此之外都是簡單暴力的狀態機，
放一下那時候報告畫的 state diagram 給大家笑一下，根本大雜燴什麼都攪在一起。  

<!--more-->

![RSA state diagram](/images/verilator/RSAstate.jpg)

Debug 一開始是用邏輯分析儀把波形倒出來慢慢 debug，然後根本一團悲劇；
後來就是靠強者我同學 johnjohnlin 提供了 python script 幫忙計算 RSA 中間值
（是的，正是 repository 裡面的 [python script](https://github.com/yodalee/rsa256/blob/master/script/RSA.py)）
，再配合 testbench 跟 iverilog 倒波形，從晚上 7 點除錯到早上 7 點差點起痟，弄完之後回去吃早餐睡覺，有夠可悲。

這次我們按步就班，依序實作 c-model、system-c 再到 verilog，verilog 也強制使用 valid/ready 的架構，模組化完整得多。
現在如果要把 Montgomery Reduce 的 R 從 2 升成 4, 8, 甚至 16，應該都是小菜一碟。  
不過話說回來，無論是大學時代實作 RSA256，還是現在實作 RSA256，唯一共同的一件事，大概就是都靠強者我同學 johnjohnlin 罩，
這次要是沒有 johnjohnlin 的幫助，我自己大概是幹不出模擬 verilog 的 C++ header 吧；
另外 verilog 的 valid/ready protocol 和 Pipeline module 也是 johnjohnlin 傳授給小弟的。

言及至此趕快看一下 github 的 insight，好險我的貢獻還是比較多。

![RSAcontributor](/images/verilator/RSAcontributor.png)

# 收尾

後來這篇文順利投稿 [2023 年的 COSCUP]({{<relref "2023_coscup">}})，在硬體軌講了一場。  
本來應該是要在 COSCUP 前把這篇系列文給打好的，但進到 2023 年之後真的覺得不知道是不是腦霧，總覺得工作效率降低了不少。

這個 project 目前應該就這樣子了，如果真的~~想不開~~要做下一步，我想可能可以來試試看 SkyWater 下線。  
介面的部分，網路上有看到一些開源實作的 AXI bus 與 SPI slave device 聽說是有 tapeout 過驗證的，
應該可以直接拿來用，第一步也許先在 FPGA 上面測試一下。
不過據 johnjohnlin 的說法，下一步的合成跟繞線，他點開開源的合成工具…然後就沒有然後了。

也是可以理解啦，開源工具如果沒有商業力量主導，很容易做出一些很龐大的東西，功能普通稍微可用，但就是原始碼幾乎改不動，還會愈改愈改不動。

不過就先等我哪天提起動力把 RSA 跟 AXI 整好再來談了。