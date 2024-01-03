---
title: "用 verilator 輔助數位電路設計：前言"
date: 2023-02-08
categories:
- verilog
tags:
- verilog
- verilator
series:
- verilator
forkme: rsa256
latex: true
---

有三個月沒有寫新文了，不過沒關係，~~這裡不像吉他英雄頻道一樣有人會催更新~~。  
故事是這樣子的，最近小弟的生活出現天翻地覆的變化，在忙各種搬家啦什麼的，都沒時間好好寫 code，
一月月初跨年、月中在三年的閉關之後出發去日本待了 10 天，回來月底接著過第二個年，什麼我的一月怎麼不見了？？？

這系列的主題要講電路驗證工具 verilator，本來這篇的標題是 **在 2022 年應該要如何開發數位電路**，
一直拖就拖到 2023 年，然後說真的，verilator 在取代現有的商用工具上應該還是不夠給力，
各大晶片設計公司也應該都有自己一套開發的流程（沒有的公司是做不出像樣的晶片的），
沒什麼稱做*應該*的理由，所以就改成現在這個標題了。
<!--more-->

當然，針對原本這種問句式的標題，都 2023 年了當然是要交給最流行 chatGPT 來回答了：

![chip_fabrication](/images/verilator/chipfabrication.jpg)

等等不是這個意思，我是要設計晶片不是要真的做，又不是要開台GG；而且熱壓機是什麼鬼，晶片吐司嗎？

再來一次：

![chip_design](/images/verilator/chipdesign.jpg)

這次好多了，不過為什麼會有繪圖軟體？可能是在說畫 layout 的工具吧，~~我記得我都用小畫家畫 layout~~

總之在這系列文章，會介紹我從大約 10 月底開始的一個專案，探索怎麼有效率的利用 verilator 這套開源工具，
來輔助硬體設計的開發，這系列文是個三個月成果的總結。  
這次開發的專案是大約是 2010 秋天（哇靠 12 年前了），在大學修數位電路設計時的一個作業，實作 256 bits 的 RSA 演算法；
不過我只實作 RSA core 的部分，給定三個 256 bits 的數字 m, e, N，輸出：
$ m^e\mod N $，並只用 verilator 來開發驗證，不會實作 $ I^2C $ 介面，也不會燒到[我手上的 FPGA](https://yodalee.me/categories/fpga/)去跑。

一般來說，做晶片因為成本巨大，一定會需要模擬工具的配合，否則硬著頭皮做出晶片結果不會動，那可真的是把錢往水溝丟。  
比較知名模擬的工具包括 Cadence 的 ncsim 跟 Synopsys 的 vcs，
[以前使用過的 iverilog]({{< relref "verilog4" >}})
跟本回主角 [verilator](https://www.veripool.org/verilator/)。  
當初是 johnjohnlin 介紹我使用 verilator 的，他的 blog 也有三篇[介紹如何使用 verilator 的文章](https://ys-hayashi.me/2020/12/verilator/) ，我斷言絕對是目前繁體中文最詳細的介紹了。  
當你手上沒錢或是單純想玩玩硬體的話，verilator 基本上毫無懸念遠超越 iverilog，
但 verilator 的使用也比 iverilog 再稍微複雜一些，也因此我們這篇裡會對它加上許多改良。  

目前我大致規畫有下列幾個主題，涵蓋不止 verilator，還包括用來驗證的軟體工具與環境，
這也是為什麼我會想下標*在 2022 年應該要如何開發數位電路*：

1. [c-model 與 systemc]({{<relref "verilator_cmodel">}})
2. [verilator framework]({{<relref "verilator_vtuber">}})
3. [systemverilog]({{<relref "verilator_systemverilog">}})
4. [後記]({{<relref "verilator_ending">}})

不過呢，看這個態勢大概又要拖稿啦，但至少我們前言發出來了，看倌們可以置板凳期待一下了。
