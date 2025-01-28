---
title: "數位電路設計系列 - 前言"
date: 2023-11-16
categories:
- ICdesign
tags:
- ICdesign
series:
- ICdesign
---

故事是這樣子的，在睽違多年之後，最近又回頭去摸了數位電路設計與 tapeout，一個我已經疏遠許久的領域，在 11/13 的時候，
以壓線之姿送出人生第一顆數位電路晶片，寫這篇序文用來記錄未來相關的發文。  
<!--more-->
上次玩數位電路設計已經是大學時代了，連這個 blog 都還沒開始寫，就知道那是多古早以前的事了。  
會想寫這篇文章，是因為在這次的下線過程中，我發現網路上相關記錄的文章相當少，搜尋到的文章不是簡中就是英文，
繁中比較詳細的大概只有[皓宇的筆記](https://timsnote.wordpress.com/digital-ic-design/)，
再來就是和大學同學們求救，11/13 出去這顆也是有賴同學們的鼎力相助，
包括長期合作伙伴 JJL 及從大學、研究所一路抱大腿抱到現在的 phoning，
在實作過程中幾乎都是摸著石頭過河，還不小心被沖走好幾次。

這其實是一件很怪的事啦，我們不是號稱矽島、晶片島、世界第一的半導體王國，結果討論文章美國大學的教材量還比繁體中文還多還新；
然後從 IC 設計來看，近期幾個新創的數位 IC 像礦機、AI 晶片都是中國美國做的，那台灣的數位電路設計人才都上哪去了？  
本著為後人開路的精神，決定把我這一路 tapeout 的過程給記錄下來，雖然小弟還是剛入門的小白，還是冀望能多留一些文章，
讓後人能有個依循，如果能解答大家的疑惑，或是讓大家少撞幾次牆，這些文章就有它們的價值了。  

當然，積體電路博大精深，絕對是人類發明中最複雜的一個，
能各方面面面俱到的人絕對是鳳毛麟角，如果文章裡面出現任何的錯誤還請不吝指教，
我也不管什麼面子裡子的，我不知道我就說我不知道~~三壘~~，好過假裝知道結果誤人子弟。

----

目前大致想到可以寫的文章、大綱如下，目前還沒有規劃到底會寫多少篇，會設單獨的[一個 category]({{< relref "/categories/ICdesign" >}})收集此類文章：

* [下線流程概述]({{< relref "chipflow" >}})  
介紹整個下線過程中要做的事，包括 verilog/simulation、synthesis、post-synthesis simulation/LEC、APR、
Post-layout simulation、DRC/LVS verification。
* [Design Compiler]({{< relref "designcompiler" >}})  
介紹 synopsys 公司的起家厝 [design compiler](https://www.synopsys.com/implementation-and-signoff/rtl-synthesis-test/dc-ultra.html)，大致的設定以及他們的意思。
* [APR：晶片的物理架構]({{< relref "chipstructure" >}})  
介紹晶片的內的架構，如 pad、鎊線、memory、power ring、power strip 等，讓大家了解 APR 到底在幹嘛。
* APR：Innovus 設定流程：  
大致走過 APR 需要的流程，這次使用的工具是 cadence 家的 [Innovus](https://www.cadence.com/zh_TW/home/tools/digital-design-and-signoff/soc-implementation-and-floorplanning/innovus-implementation-system.html)，
所以就對不起啦 synopsys 的 [ICC2](https://www.synopsys.com/implementation-and-signoff/physical-implementation/ic-compiler.html)，
文中會走過大部分 layout 需要的檔案，並提點一下此次 layout 中遇到絆倒我的石頭（而且還很多顆，氣死我）。
* Verification：  
DRC 與 LVS，沒想到這麼多年之後，連我自己都做過 DRC engine 之後，換成要來解工具吐給我的 DRC violation。  
而且都是貨真價實的 violation 不是什麼 Missing violation 還是 False violation；還要去看 LVS 那個 GY 的笑臉。