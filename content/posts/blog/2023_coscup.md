---
title: "2023 COSCUP"
date: 2023-08-03
categories:
- LifeRecord
- hareware
tags:
- RSA256
- verilog
- COSCUP
series: null
---

COSCUP 2023
又到了一年一度大拜拜的時候了，經過[去年全員戴口罩的第一次實體]({{<relref "2022_coscup">}})，
今年完全解封感受得出氣氛輕鬆很多，外國人也來了不少。  
自從 COSCUP 免費之後可以看出規模有一年比一年大的感覺，今年研揚已經開到六樓都全滿了，再來不會要開另一棟大樓吧。  
今年也推坑沒參加過 COSCUP 的人來參加一下，幫 COSCUP 增加一些生力軍，他主力在語言相關的議程還有 k8s 等等；現在正在推坑他明年也來投稿一下XD。
<!--more-->

# 演講議題

今年回到硬體議程軌，也是去年十月開始執行的題目[RSA256：用 verilator 驗證與測試的硬體模組](https://volunteer.coscup.org/schedule/2023/session/3RY9JG)，與強者我同學裕盛一起實作的硬體 RSA256。  
這個 project 一部分是因為工作轉換，會需要充實硬體設計方面的知識，
剛好藉著這個 project 從硬體業界的裕盛身上偷一些經驗出來，目前看來是有達成它本來的目的。  
投這個題目也是一種必中的策略，今年的硬體軌台灣的講者也只剩下我們這組了
（當然也有些講硬體的但不在我們這軌，例如各種開源議題的 [Make Your Own Ray Tracing GPU with FPGA](https://pretalx.coscup.org/coscup-2023/talk/QYPYUG/)），裕盛就說得很明白：

> 我才不信不會上，你那個沒上的唯一原因大概是整個軌被取消(X

同時裕盛自己也從這個 project 的衍生物 - 一個模擬 verilog 的 C++ class - 投稿了另一個題目
[C++ boost hana的分析以及在資料處理上的應用](https://pretalx.coscup.org/coscup-2023/talk/FCXLBD/)，一魚兩吃成就達成。

參加完 COSCUP 才發現原來我 [blog 的文章]({{< relref "/series/verilator">}}) 還沒打完，真慘；進到 2023 年之後真的覺得不知道是不是腦霧，總覺得工作效率降低了不少，你看 blog 上面的文章也少超級多，該來加油把文章補完了。

回顧一下過去投稿的紀錄：
* 2019 年：PEG parser 和 Nixie Tube
* 2021 年：Rust Gameboy Emulator
* 2022 年：Rust rrxv6 OS

也難怪我在講完今年的議程之後，有聽眾湊上來問說：

> 我參加這麼多年，看你題目變化這麼廣，想請問你是自學硬體相關的部分嗎？

歹勢，其實我是學硬體出身的，真要說如果我研究所沒亂跑，現在可能在電子業輪班，但因為學了軟體所以不務正業，RSA256 這題目應該是我本業才對，結果還是靠抱我同學大腿才做出來。

## [部落格文章集，待完成]({{< relref "/series/verilator">}})

## 投影片

{{< rawhtml >}}
<iframe src="https://www.slideshare.net/slideshow/embed_code/key/gWA6FA3unONc5T?startSlide=1" width="597" height="486" frameborder="0"   marginwidth="0" marginheight="0" scrolling="no" style="border:1px solid #CCC; border-width:1px;   margin-bottom:5px;max-width: 100%;" allowfullscreen></iframe><div style="margin-bottom:5px"><strong><a href="https://www.slideshare.net/youtang5/coscup2023-rsa256-verilatorpdf" title="COSCUP2023 RSA256 Verilator.pdf" target="_blank">COSCUP2023 RSA256 Verilator.pdf</a></strong> from <strong><a href="https://www.slideshare.net/youtang5" target="_blank">Yodalee</a></strong></div>
{{< /rawhtml >}}

# 參加心得

## 聽講

今年選的題目其實滿少的，雖然在日記本上寫滿了有興趣的題目：
![schedule](/images/posts/coscup2023.jpg)

但最後聽的其實沒那麼多；第一天真的就是在場裡面亂晃，用手機挑一些有興趣的題目；第二天則是主力在 Hardware 議程軌，
這軌因為跟外國的硬體專案合作，弄得很像大學時代的電子電路課程，特別簡報用的講義真的很有教學的風格。

COSCUP 最大的一個痛點仍然是午餐，暑假+週末學校餐廳通常會減半營業，今年又遇上台科大最近的那間餐廳在暑假整修，
以致於我們兩天都吃摩斯漢堡（雖然一天吃基隆路上的一天吃校內的）。  
另一個痛點大概是網站上的議程表實在不好用，但因為 COSCUP 開的議程軌實在太多了，我覺得這實在不是一個簡單的題目。

## 疫情

2023 年疫情真的是沒什麼影響了，雖然聽說在 COSCUP 之後有一波 COVID 在聽眾與講者間暴發，不過也就小感冒吧，
我個人是在七月初就已經中過一次，現在抗體量應該是高到無敵狀態，~~是 COVID 怕我不是我怕 COVID~~。

# 展望明年

我後來發現一個 COSCUP 不錯的時程表：
* 8-10 月左右開始訂題目，發想想做什麼，題目的尺寸不要太大要大概 5-6 個月能執行完的。
* 10-4 月全力執行
* 5 月完工之後剛好接上 COSCUP 的投稿，6-7 月做投影片

我投過的題目包括 Nixie Tube、Rust Gameboy Emulator、rrxv6 都是照著這個時程弄出來的，如果有人想要挑戰投稿的話可以參考看看。

現在也差不多可以來想想明年可以做什麼了，現在口袋裡有幾個提案：

## RSA256 延伸
今年的 RSA256，把裡面的 systemC 取代掉換成自己的模擬系統，我們後來發現 SystemC 上真的有些設計不良，相依性太重又沒辦法精確重現 verilog 的行為，會遇上一些時序上的問題。  
這部分現在也在 [RSA256 dev branch](https://github.com/yodalee/rsa256/tree/dev) 上實作中，不過這部分比較會是裕盛的功，應該是讓他去講。

## RSA256 SkyWater 下線

把 RSA256 拿去 SkyWater 下線，但這個應該沒那麼簡單，還有很多亂七八糟的東西沒處理，像是 AXI bus、周邊介面等等；
然後要學會怎麼用 SkyWater 那堆合成、佈線用的工具，據裕盛的經驗，光載下來執行就浪費一堆時間遑論真的去產出有價值的東西。  
而且要做的話要快，從真正的 tapeout 到回來量測要花很多時間，也許展望 2025 再講會比較妥當。

## 完成 rrxv6
今年 Day 1 Prime Session [Writing a technical book doesn’t have to be scary](https://pretalx.coscup.org/coscup-2023/talk/8GEEAR/) 是講如何出書的，
另外第一天的下午也有一場 [Tenok: 打造用於機器人控制的微型即時作業系統](https://pretalx.coscup.org/coscup-2023/talk/XA9XJC/)，這場講者的氣場有夠強，非常生猛。  
聽了這兩場的啟發，讓我想到我手上也有個卡在半路上的 [rrxv6](https://github.com/yodalee/rrxv6) 
還沒完成，其實不是真的沒動，在六月初也是完成了 virtio 的設計，COSCUP 結束可以繼續往下動了。  
打算如果完成 rrxv6 的話，可以考慮明年報一場講 RiscV 的硬體設計如 PLIC 和記憶體等等，
但感覺會有點像 Computer Architecture 的課程XD；或是像 Tenok 一樣，專注在作業系統如何設計上。  

完成這個專案也可以考慮要不要試著出本書，不過先完成比較重要，超忙的 7 月剛結束，可以捲起袖子繼續來開發了。

## 另一個硬體專案

完成了 RSA256 之後，也有考慮一下另外的硬體專案，目前是有考慮選一個小巧可以驗證概念的專案出來玩，
例如上面提到的 Ray Tracing ，或是做個 zk prover。

但再想想吧，慢慢想到一個好的題目總比快快想結果做不出來好，如果看倌們有想到什麼適合我去實作的題目也可以留言讓小弟參考一下，
不然小弟明年大概要老實的當個聽眾了。