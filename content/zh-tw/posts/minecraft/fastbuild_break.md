---
title: "Minecraft plugin fastbuild break"
date: 2014-02-23
categories:
- minecraft
tags:
- minecraft
series: null
forkme: fastbuild
---

這篇接續[上一篇]({{< ref "fastbuild_build.md">}})最近花了一點時間，把fastbuild plugin本來預定的功能寫完了。  
至於為什麼會相隔這麼久(16天)，因為作者平常~~都在打東方~~有很多事情要忙，加上Java實在不是作者熟悉的語言，以致進度緩慢。  
這次主要寫的是break的部分，原始碼比place 的listener多了一倍，因為break還涉及手中工具的耐久度設定、是否要掉下東西等，功能更複雜。  
<!--more-->
廢話不多說，來看看怎麼設計。  

### Event Handler

首先我們要聲請監聽票的event是BlockBreakEvent，這個event會在block被破壞的時候呼叫。 這個event會包含資訊有：玩家，被破壞的方塊。  
為了要做到fastbuild的功能，我另外監看了PlayerInteractEvent，可以從這個事件中取得，玩家是碰到方塊的哪一個面。  
因為plugin只能做到event based，因此這個plugin還是有一點限制，我們不能讓使用者邊敲方塊，後面一整排的方塊都開始出現裂痕，只能處理BlockBreakEvent(方塊已經爆了)，再把後面的方塊設成空氣。  
這樣會產生一個問題：如果使用者用鏟子爆了泥土，可是後面是石頭，這樣不就可以用鏟子當超強挖礦工具？  
所以這裡我們限制會一起挖的，只能是同樣類型的block。   
```java
for (int i = 0; i < n-1; i++) {
  nextBlock = block.getRelative(face);
  //currently only deal with same type block
  if (nextBlock.getType() == originType) {
    Collection drops = getDrops(tool, nextBlock);
    nextBlock.setType(Material.AIR);
    if (!isCreative) {
      // drops
      createDrops(nextBlock, drops);
      // durability
      if(!reduceDurability(tool,player)) {
        break;
      }
    }
  } else {
    break;
  }
}
```

### Durability:
這部分參考[2-3]({{< relref "#reference" >}})，透過`ItemStack的setDurability()`跟`getDurability()`去設值，要注意的是durability值愈高表示工具愈爛，並且可以用 `ItemStack.getType().getMaxDurability()`，來確定工具壞了，以免工具只能挖一格，卻把20格都挖掉了。  

### Enchantment:
我們處理的enchantment有unbreaking跟silk touch，分別影響durability跟drop items。  
minecraft裡物品的item max durability值是恆定的，unbreaking只是在增加durability 時加上一個機率，有一定的機不扣durability，在這裡我們複製這個設定。  
可以透過 `ItemStack.getEnchantmentLevel(Enchantment ench);` 來取得enchantment的值，非 0 表示有enchantment。  

### drops:
這裡我們呼叫 block.getDrops(ItemStack) 來產生drop items內容，用這個的好處是，它會自動判斷工具的等級高低，像用木鎬挖鐵礦，這個事件就會回傳空的內容。
不過它不會處理工具有Silk touch的狀況，因此有Silk touch的時候要自己把原本的方塊傳回去。  
最後再利用`World.dropItemNaturally(Location, ItemStack)`產生drop items即可。  

## Demo:
{{< youtube qWxviuqtntw >}}
這個是用gtk-recordMyDesktop錄的，聲音好像比畫面還要慢一點，我也不知道問題在哪lol。    

## 原始碼：
本程式公開所有原始碼，遇到bugs歡迎修改後丟pull request  
[FastBuild](https://github.com/lc85301/FastBuild)

## 參考資料 {#reference}

1. [Bukkit API Overview](http://jd.bukkit.org/)，要寫plugin不看這個不行www  
2. [Minecraft Wiki enchantment](http://minecraft.gamepedia.com/Enchanting)  
3. [Minecraft Wiki tools](http://minecraft.gamepedia.com/Tools)