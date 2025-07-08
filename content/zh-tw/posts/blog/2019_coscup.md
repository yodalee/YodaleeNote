---
title: "第一次在 COSCUP 當講者就上手"
date: 2019-08-19
categories:
- LifeRecord
tags:
- NixieClock
- rust
- COSCUP
series: null
---

故事是這樣子的，在上周結束了兩天的 COSCUP 行程，總算達成人生成就：參加 COSCUP (欸。  
這次是以講者的身分去的，畢竟搶票什麼的實在是太難了，就跟搶普悠瑪一樣難，當講者好像比較簡單（True Story）。  
<!--more-->

這次準備的題目其實都是準備許久的，一個是本次 COSCUP 有開 Rust 議程軌，就把之前寫 computationbook-rust 裡面當範例的 simple language ，配上研究一小段時間的 PEG parser 挑出來，攪一攪投出去。  
本來這是想要去年的 MOPCON 投的，但畢竟 MOPCON 是以網路為主體，跟這 programming language 還是格格不入被拒絕了。  

下面是投影片：  

{{< rawhtml >}}
<iframe src="//www.slideshare.net/slideshow/embed_code/key/JZO90DpXew5ERO" width="595" height="485" frameborder="0" marginwidth="0" marginheight="0" scrolling="no" style="border:1px solid #CCC; border-width:1px; margin-bottom:5px; max-width: 100%;" allowfullscreen> </iframe> <div style="margin-bottom:5px"> <strong> <a href="//www.slideshare.net/youtang5/use-peg-to-write-a-programming-language-parser" title="Use PEG to Write a Programming Language Parser" target="_blank">Use PEG to Write a Programming Language Parser</a> </strong> from <strong><a href="https://www.slideshare.net/youtang5" target="_blank">Yodalee</a></strong> </div>
{{< /rawhtml >}}

blog 的話，可見：
1. [實作麻雀雖小五臟俱全的程式語言]({{< relref "2018_rust_simple.md">}})
2. [剖析表達文法 PEG 簡介]({{< relref "2018_PEG.md">}})
3. [使用 rust pest 實作簡單的 PEG simple 剖析器]({{< relref "2018_rust_pest_PEG.md" >}})
4. [使用 procedence climbing 正確處理運算子優先順序]({{< relref "2018_rust_precedence_climbing.md">}})

另外一個議題則是去年 8-10 月做的 Nixie Tube Clock，COSCUP 有非常適合的硬體議程軌，
老實說 Rust 議程軌我覺得不一定會上，硬體議程軌我就真的滿確定會上，畢竟講硬體的本來就少，Nixie Tube Clock 也滿完整的，果然最後就上了一場。  
投影片在此：  

{{< rawhtml >}}
<iframe src="//www.slideshare.net/slideshow/embed_code/key/11K9jKO6FS1aym" width="595" height="485" frameborder="0" marginwidth="0" marginheight="0" scrolling="no" style="border:1px solid #CCC; border-width:1px; margin-bottom:5px; max-width: 100%;" allowfullscreen> </iframe> <div style="margin-bottom:5px"> <strong> <a href="//www.slideshare.net/youtang5/build-yourself-a-nixie-tube-clock" title="Build Yourself a Nixie Tube Clock" target="_blank">Build Yourself a Nixie Tube Clock</a> </strong> from <strong><a href="https://www.slideshare.net/youtang5" target="_blank">Yodalee</a></strong> </div>
{{< /rawhtml >}}

blog 筆記總計有十篇：  

0. [前言]({{< relref "posts/nixie/introduction" >}})
1. [材料取得]({{< relref "1material.md" >}})
2. [自組高壓電路]({{< relref "2hv.md" >}})
3. [驅動電路]({{< relref "3driver.md" >}})
4. [控制電路]({{< relref "4control.md" >}})
5. [電路板基礎]({{< relref "5PCBbasic.md" >}})
6. [電路板實作 layout]({{< relref "6PCBimpl.md" >}})
7. [焊接]({{< relref "7weld.md" >}})
8. [寫 code]({{< relref "8code.md" >}})
9. [後記]({{< relref "ending.md" >}})

個人小小的體悟是，先不要想 COSCUP，先想著把某件事情做好，時候到了投稿自然會上；
就像會上一位大大說的，因為沒搶到票決定每周用 golang 寫一個 project，52 週之後就當講者了。  

這次投上的題目，無論是 PEG + programming language，還是 Nixie Tube Clock，都是一年前甚至兩年前開始的嘗試，
PEG 還搞了個失敗的 C parser，blog 寫了好幾篇的題目，做到這種程度才能換到 40 分鐘的上台時間；也許現在就該來想一下要做什麼新題目了。  

----  

第一次參加 COSCUP ，這次真的融合了超多議程軌人超級多，據說直接突破 2000 人，大拜拜的意味滿重的，
像 Pycon 這樣同時段 3 場的都很常兩場一定要選的，COSCUP 同時開 14 場議程，從一開始聽議程就不是目的了。  
實際下來比較像：**三分聽議程，七分面基友**。  

細數一下我到底遇到多少在網路上見過面的大大：
* 像是從荷蘭遠道而來的呂行大大
* 台灣軟體界照世明燈郭神大大
* 久未見面的 jserv 大大
* 好高興教授大大
* TonyQ 大大

在會前酒會遇見
* 在上海大殺四方的 Richard Lin 大大
* 曾經在高雄氣爆的時候幫我提升 Google Map 權限的 pingooo 教授大大
* 認識了台灣 maker 社群
* Python HsinChu User Group - PyHUG。  

不過我覺得比較扯的還是呂行大大，走一走每個攤位都能遇到人，真的是神猛狂強溫爽發。  

記得以前參加 PyCon，總會在那邊要求自己盡量的聽，連可能不知道在講什麼的、 lightning talk 都聽完之類的，這幾年終於改掉這樣的習慣，發現時間寶貴，聽一些跟自己太遠的東西其實是浪費時間，還不如放點時間出來跟大家聊聊天，真的沒想聽的就早早離開會場沒差；網路上常講：  

> 小孩子才做選擇，成年人當然是我全都要。  

但其實，成年人才知道自己要什麼、不要什麼、有能力要什麼、沒能力要什麼，我覺得是反過來的：  

> 成年人才做選擇，小孩子才是我全都要。  

我想最後還是要感謝一些人，像是強者我同學 JJL 大大幫小弟 review 投影片；強者我同學 wmin0 大大幫小弟生出一個 Nixie Tube 的講題，這個題目應該給大大講才是。  

明年希望大家也都能成為 COSCUP 講者。  
