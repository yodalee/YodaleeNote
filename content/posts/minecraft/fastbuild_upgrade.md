---
title: "一樁因為版本升級引發的慘案"
date: 2016-05-23
categories:
- minecraft
tags:
- minecraft
series: null
---

Minecraft升上1.9板已經有一段時間了，因為1.9版加入了戰鬥功能，玩家能在左手跟右手上放置不同的物品，也因此造成了一些悲劇。   
故事是這樣子的，之前寫的[Minecraft plugin fastbuild]({{< ref "fastbuild_build.md">}})，放置方塊時可以大量放置的功能  
<!--more-->
設計上我是先取得玩家手上的物品，一個ItemStack 的物件。  
計算所能放置的數量，從ItemStack 減去放置的數量，再call API將玩家手上的物品設為ItemStack。  

問題出在現在Minecraft 1.9允許有兩隻手，如果將物品放在左手，則放置會將右手設為ItemStack，若右手空手就變成憑空複製物品。  

解決方式是判斷玩家在放置物品是從左手放還是右手放，在設定手上物品時設定為玩家使用的那隻手，新的API 針對兩種手有不用的設定function，用新的API 解掉即可。  
不過在修掉之前，server 上已經有人用這樣的複製功能弄了一大堆鑽石磚，還在我家旁蓋了一座鑽石塔，根本嘲諷點滿了XD (不過這座塔因為衝到旁邊的建案，應該會被我都更掉)  
![upgrade1](/images/minecraft/upgrade1.png)
![upgrade2](/images/minecraft/upgrade2.png)
總之，當主程式和API 的不斷更新的時候，自己寫的程式是也要時時跟上最新，否則不知不覺中就會噴出bugs 來。  

當然這樣的升級也不是不好，之前每個block 的型態是用 int 來表示，要比對型態就要自己去查每個物品的編號，新版的API 已經將所有物品用Enum 再包一層，使用真實名字來代表物品，撰寫時不再需要自己查編號值，相對來說好寫得多。