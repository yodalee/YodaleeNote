---
title: "自幹世界線變動率探測儀（Nixie Tube Clock）：前言"
date: 2018-10-18
categories:
- hardware
tags:
- hardware
- NixieClock
series:
- 自幹世界線變動率探測儀(Nixie Tube Clock)
forkme: nixieclock
---

總之先秀個成品：  

![final](/images/nixie/DSC_1155.jpg)

看過 Steins;Gate 一直想自幹一個世界線變動率探測儀，這個點子其實有點久了，不過也就只是一直放著而已，畢竟學生時代沒什麼錢也沒什麼時間下手。  
直到最近因為 Steins;Gate 0 開始播送，強者我同學小新大大跟強強林大大也生出想來做一個的念頭，手頭上也比較寬裕了些，於是三人一起怒做一陣，所以整個九月跟十月初除了看書之外都沒有在寫 code，功力退步十年 QQQQ，這裡也沒在發文都要長草了。  
不過大家放心，接著就是開發過程記錄的 N 連發，保證把這裡的草都除到連基岩都露出來。  
<!--more-->

輝光管（nixie tube，或譯數碼管，好像沒有統一的譯法，但我覺得輝光管比較符合它的發光原理）總之就是個1950年代的玩意，現在大概只有懷舊狂會去用它，都買不太到了，ebay 上有一些舊蘇聯國家的賣家在賣，大部分都是拆下來的二手管，價格都貴到靠北，我買的已經算比較便宜的，如果是新管會貴上一倍。   
![nixie tube](/images/nixie/DSC_1161.jpg)

輝光管要高壓驅動，相較現今成熟的顯示技術，消耗功率大、體積大、可視角度窄、還要高壓驅動，七段顯示器出來之後都被淘汰光了，可預期這東西的價格會一路走高（其實我很懷疑2036年還買得到這種東西）。在找相關資料的時候，是有在 [kickstarter](https://www.kickstarter.com/projects/popshields/smart-nixie-tube) 上看到有人要製造新的輝光管，但出貨之後似乎沒有持續製造販售。  

做這個會遇到一籮筐的問題，決定就在這裡記錄一下開發流程，按照所謂的開源慣例，本作品所有內容都公開在 [Github](https://github.com/yodalee/NixieClock) 上面，包括硬體的 Layout Schematic、Layout Gerber 檔跟軟體的 Arduino 程式碼，歡迎大家來提意見，如果有什麼問題也歡迎提出。  

下面是本系列所有文章的連結：  
1. [材料取得]({{< relref "1material.md" >}})
2. [自組高壓電路]({{< relref "2hv.md" >}})
3. [驅動電路]({{< relref "3driver.md" >}})
4. [控制電路]({{< relref "4control.md" >}})
5. [電路板基礎]({{< relref "5pcbbasic.md" >}})
6. [電路板實作 layout]({{< relref "6pcbimpl.md" >}})
7. [焊接]({{< relref "7weld.md" >}})
8. [寫code]({{< relref "8code.md" >}})
9. [後記]({{< relref "ending.md" >}})
