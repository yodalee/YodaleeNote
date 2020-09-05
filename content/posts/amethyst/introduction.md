---
title: "使用 Amethyst Engine 實作小行星遊戲 - 目錄"
date: 2020-06-24
categories:
- rust
- amethyst
tags:
- rust
- amethyst
series:
- 使用 Amethyst Engine 實作小行星遊戲
---

故事是這個樣子的，之前因為武肺的關係耍廢了一陣子，你看 blog 都沒更新幾個月了，只有中間在那邊玩 vscode 整個就是魯廢。 最近受到強者我同學在歐陸大殺四方的呂行大神感召，試玩了一下 Rust 的 amethyst （紫水晶，託名字的福一定要查 rust amethyst 才會查到要的東西）框架，決定來寫點文介紹一下。  
<!--more-->

當初看到 amethyst 是在 rust 的 [are we game yet 頁面](https://arewegameyet.rs/)上看到的，
如果你只是要寫簡單遊戲的話，rust 有另一套也算知名的引擎 [Piston](https://github.com/PistonDevelopers/piston)，用量目前比 amethyst 還要高一截。  
但我覺得 piston 的潛力不及 amethyst，雖然完整但 piston 在虛擬化上面沒有 amethyst 這麼高階，導致很多東西還是要設計師自己跳下去設計，相對來說就是學習曲線比較淺，有經驗的話看看文件就能上手。  

不過，現下一般來說找不太到用 piston 或 amethyst 寫的大型遊戲，在範例頁面兩者做的都只是些老遊戲的重製；
不過話說回來做遊戲本來跟遊戲引擎就沒什麼關係，比較像是你整體企劃跟資源有沒有弄好，沒引擎還是可以寫個爆紅的 2048 或 flappy bird，有了好引擎還是會搞出歷史性的糞作，像是最後生（消音。  

總而言之 amethyst 是（另）一套遊戲框架，背後的設計邏輯是所謂的 ECS：entity、component、system，是有人說 ECS 在 gaming 有 buzzword 的意味，但畢竟兩個比較大的遊戲引擎：unity 跟 unreal 都用上了 ECS 的概念，我想這部分應該是沒什麼疑慮。  

在這個系列文，我預計會用 amethyst 寫一個打小行星的經典小遊戲，先聲明這的專案是從這個[同樣的專案](https://github.com/udoprog/asteroids-amethyst)複製而來，
它也是用 amethyst 寫的，只是年代久遠現在已經編不起來了，我直接拿了它的素材來用（應該是不至於被吉吧Orz），完成的畫面應該會如下所示：  
![finalscreenshot](/images/amethyst/finalscreenshot.png)

如果去看 amethyst 的教學文，它有用 amethyst 寫一個 [pong 遊戲](https://book.amethyst.rs/stable/pong-tutorial.html)，但我覺得 pong 不算一個好的例子，它不會生成跟刪除新的物體，偏偏這應該是很多遊戲必備的功能，用打小行星這種比較能示範怎麼做。  
總之讓我們開始吧，這篇就作一個目錄的角色，用來連接所有教學文，希望能對大家成功傳教（欸。

下面是本系列所有文章的連結：  
1. [設定專案]({{< relref "1setup.md" >}})
2. [讀入資源]({{< relref "2resource.md" >}})
3. [連接輸入]({{< relref "3input.md" >}})
4. [移動物體]({{< relref "4moveobject.md" >}})
5. [生成物體]({{< relref "5spawnobject.md" >}})
6. [刪除物體]({{< relref "6deleteobject.md" >}})
7. [亂數]({{< relref "7random.md" >}})
8. [使用ncollide2d實作碰撞]({{< relref "8ncollide.md" >}})
9. [UI]({{< relref "9ui.md" >}})