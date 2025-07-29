---
title: "疫情後第一次實體 COSCUP"
date: 2022-08-03
categories:
- LifeRecord
- hareware
- rust
- operating system
tags:
- rust
- hardware
- COSCUP
series: null
---

人生第三次參加 COSCUP ，2021 年因為武肺大爆發，活動全部轉為線上，連我的演講也變成預錄影片最後回答問題，
[活動心得在此]({{< relref "2021_coscup_online.md">}})。  
今年在疫情後首次舉辦實體活動，也改成不用買票的形式，想聽直接到會場不會有人驗票，沒有想聽的了想走就走，
變得自由很多也不用搶票了，根本超級佛心，看看今年一樣開出了平行近 20 軌的議程，連聽都聽不完的各式講題，
論其廣度與規模，COSCUP 可說是穩坐台灣開源研討會的第一品牌了。
<!--more-->

## 演講議題

這次我準備的題目是從去年六月開工的 [rrxv6]({{< relref "/series/rrxv6" >}})，因為那時正在兩個工作間的轉換期比較閒，
就寫了一些 [Rust bare-metal]({{< ref "/series/rust-bare-metal-programming">}}) 的程式，
後來想想就直接開始了 rrxv6 專案，想用 Rust 復刻一個 RISC-V 的 xv6 kernel，結果這頭洗下去洗了一年都還沒洗完，
中間也是一堆障礙，像什麼 virtual memory 撞在 pointer 上；scheduler 撞在 lock 上。

大概三-四月，拚一口氣把 system call 給接好，把 Hello World 寫出來就決定要投稿了，畢竟這個處理好後面（應該）不會有更複雜的東西了，
最後一關大概只剩 virtio 接磁碟相關，其他都是去在原本的資料結構上面一些操作而已；
也許如果明年能完成它的話，也許可以再來投稿一個<帶你讀源碼>來介紹 xv6 作業系統。  
投稿的時候還有在想要選**中階**還是**進階**，後來想想什麼 memory allocator, pointer, mutable static 什麼的，
都是一般寫 rust 不會用到的東西，進階就給他點下去了。

以下是這次演講題目的資源，不過如果你平常就有在看這個 blog 大概也沒少看什麼吧
### [部落格文章集]({{<relref "/series/rrxv6">}})
### 投影片
{{< rawhtml >}}
<iframe src="//www.slideshare.net/slideshow/embed_code/key/5sRJDRcNk9OYGs" width="595" height="485" frameborder="0" marginwidth="0" marginheight="0" scrolling="no" style="border:1px solid #CCC; border-width:1px; margin-bottom:5px; max-width: 100%;" allowfullscreen> </iframe> <div style="margin-bottom:5px"> <strong> <a href="//www.slideshare.net/youtang5/rrxv6-build-a-riscv-xv6-kernel-in-rustpdf" title="rrxv6 Build a Riscv xv6 Kernel in Rust.pdf" target="_blank">rrxv6 Build a Riscv xv6 Kernel in Rust.pdf</a> </strong> from <strong><a href="//www.slideshare.net/youtang5" target="_blank">Yodalee</a></strong> </div>
{{< /rawhtml >}}

## 參加心得

### 場地
今年 COSCUP 一樣假[台灣科技大學](https://www.ntust.edu.tw/) 研揚大樓跟其他一些大樓舉辦，
據我在會前派對上的了解，其實是我 2019 年 [第一次參加]({{< relref "2019_coscup.md">}})那年，
第一天用的國際大樓跳電臨時把第二天的議程都拉去研揚，結果用過之後就回不去了改成年年在研揚，
美中不足的一點是研揚缺乏可以裝百人以上可以當開場的大教室，必須拉去其他大樓舉行，
今年主議程軌所在的 RB105 跟次議程軌所在的 AU 視聽館，與研揚大樓就有段距離，天氣又很熱移動就很麻煩。  

不過這樣也好，畢竟人數如果要再多就要開始煩惱台科大的場地會不會不夠用了，目前我綜觀台北，還真的沒想到有哪裡是比台科大更適合的。
也許台大的博雅館+普通教學館聯合起來也不錯，博雅一樓也有特大階梯教室可以辦開閉幕式，
目前感覺應該還會留在台科大幾年，畢竟今年都已經變成免費入場了，我覺得人數也沒有變多很多，
也許台灣參與活動的最大人數差不多就是這麼多了吧？  

### 疫情

COSCUP 2022 應該是疫情之後我參加過最群聚的活動了，有些人可能有去衝院線強檔，例如有人在那邊七進七出 Top Gun Maverick，
但我基本上都會等個 3-4 周再去，買票也會儘量選坐遠一點的，所以都沒那麼群聚。

COSCUP 就不然了，會前派對因為下暴雨，一群人直接塞在酒吧室內區的小空間，或是戶外區小小的遮雨棚下聊天，
而且因為狂風暴雨，即使有戴口罩我想溼掉無效的也不少。  
（我是看看下暴雨之後我就先閃了，去隔壁的佳佳甜品吃點心，然後雨就停了，笑死。）

活動中也是 50-70 人塞在一間小教室裡面（很有以前大一上邏輯設計的感覺XD），老實說混一兩個帶病毒的人進來根本再正常也不過了，
然後我記得有人一直打噴嚏 =3=；
第二天就好一點，因為我聽的硬體軌都沒什麼人在，人數一度降到個位數；
反倒是 Rust 軌工作人員一段把場地淨空進去消毒，不知道是不是有足跡了。

但話說回來，看起來大家除了口罩戴著其他是真的都不在意了，我也是因為老早室友就確診過了，什麼你說教室裡可能有人確診？
是有我室友確診每天接觸 8 小時可怕逆？

### 議程

今年 COSCUP 第一天我都在 System Software 議程軌，這軌真的是好戲一波波，從早到晚毫不間斷，
中間我有跳過一場 ML/AL 處理器相關的，去外面的 7-11 買個三明治跟果菜汁當午餐。  
說起來我們觀眾是想吃飯就不聽了出去吃，那些議程軌主持人就真的辛苦，0900 就要開始場佈，再來到 1600 最後一場都是不吃不休息，
真的累人，我看不死都只剩半條命…。

第二天上午多待在 FOSS Hardware 議程軌，這天強者我同學 JJL 也有來現場，中午他出去順便幫我買了 Mos Burger 當午餐。

第二天下午則是在 Rust 議程軌：
* 講了我自己的 rrxv6
* 聽遠在荷蘭大殺四方的~~大家都愛旅行~~呂行講 AWS Rust SDK，可惜是預錄影片而不是大大親臨現場
* 聽了 justapig9020 講 OoO processor emulator，聽到大大是因為去年我寫的 Gameboy emulator 而寫今年的 project 還是覺得滿有成就感的。

### 議題觀察

不知道是因為 [SiFive](https://www.sifive.com/) 贊助還是什麼神奇的原因，今年的 RISC-V 可以說是大爆發（其實我也貢獻了一場），
SiFive 的人講 RISC-V 的 vector extension 設計、RISC-V 上面的 ftrace 軟體設計、寫一個 RISC-V emulator 等等。
硬體也是不遑多讓，多個議程要不是與 RISC-V 直接相關如 NaxRiscv，就是在 project 裡面塞了一顆 RISC-V 的處理器。

但真的說起來的話，RISC-V 在台灣呈現軟體熱硬體冷的狀況，軟體如火如荼在玩各種 RISC-V 的小工具，
在硬體上除了 [Andes](https://www.andestech.com/tw/tw-homepage/) 已經在開發 RISC-V 的商用解決方案，
除此之外就沒看到多少使用 RISC-V 的非商用專案，這多少與 RISC-V 當初推出的理念有些背道而馳，
連帶的就是 COSCUP 第二天硬體議程軌，在下午的時候聽眾就只剩下個位數，同時場次八場有七場是連線外國講者，
唯一一位本國講者也是講 verilator 而不是 RISC-V。

個人覺得原因之一是台灣硬體的產業鍊已經非常成熟了。  
EDA 找御三家的就可以，反正三家在台灣都有設公司（可能還有研發部門）， 也都有 AE 可以諮詢，何必用 FOSS 那堆*拉基*；
架構就用拿手的 x86 或者 ARM，驅動 OS 工具鏈都完備了；
晶圓下線業界就找台積聯電、學生就找 CIC，幹嘛用 SkyWater 130/90 nm？你知道 130/90 nm 在 CIC 都是至少十年以前的東西了嗎？

這其實是大環境使然，在台灣做硬體可能是全世界數一數二簡單的，光 CIC 提供的服務就不知道值多少錢了，
在台灣唸資工碩士，只要你有想法教授又支持你的話，下線的機會可能都比國外唸電機博士還高，

就像我先前也非常疑惑，為何區塊鏈大爆發的時候，主流的礦機竟然不是台灣設計，台灣不是有全球一流的電子產業鏈？  
但正因為電子產業鏈的主流愈是強大，就愈有能力吸住一流、有能力開發全新產品的人才，進而生成正循環壯大電子產業鏈既有的內容。

電子產業的主流部分愈是堅實，反而愈不容易注意到區塊鏈礦機、 RISC-V 和 SkyWater 等主流之外的可能性，
電子台灣的優勢，也可能是台灣發展的隱憂，真的是福禍相倚，人生好難。

