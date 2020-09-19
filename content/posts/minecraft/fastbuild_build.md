---
title: "Minecraft plugin fastbuild build"
date: 2014-02-08
categories:
- minecraft
tags:
- minecraft
series: null
---

最近想要寫一個快速整地用跟建設用的minecraft bukkit plugin，畢竟在進行大建築物的建設時，常常要剷平一整個山丘，或者要鋪一整片地板，很費工夫而且很慢，按著shift後退加滑鼠右鍵也很累。  
用worldedit的確可以達成同樣的目標，可是那又太容易了。這個fastbuild的目標，就是一個威力中等的plugin，不像worldedit這麼有破壞力，保留建築材料自己取得的挑戰，又比用鐵鏟跟專注狂點右鍵更快一些，可以把精力用在建築物的設計上。  
總結來說，worldedit是要讓creative mode更creative mode；fastbuild則是要讓survival mode 更creative mode一點。  
<!--more-->
雖然已經有人寫過了類似的東西，在[參考資料1]({{< relref "#reference" >}})，但它是mod，也沒有繼續更新，大體上我的目標和它是一樣的。  

## Spec

1. 使用某個鍵或指令，目前設定是setn int，讀入使用者打入的數字。  
2. 之後破壞方塊和放置方塊時，可以一次破壞/放置該數字的方塊。  
3. 破壞/放置方塊時的方向，視破壞/放置方塊哪個面而定，破壞上面，就是向下破壞n格；放置上面，就是向上放置n格。  
4. 破壞方塊時，該數字目前先定在64，輸入超過數字會自動設在64。  
5. 破壞方塊時，若n格內有空氣方塊，則破壞會穿過該格空氣。  
6. 破壞方塊時，工具也會進行n次耐久減損判定，所以工具也要帶夠。  
7. 破壞方塊時，若用鏟子挖土，但n格內可能有岩石，這要視bukkit怎麼設計。  
8. 放置方塊時，該數字同樣先定在64，或者是放置時該stack所持有的方塊數量。  
9. 放置方塊時，若遇到其他方塊擋路，則只放到擋路方塊為止。  
10. 若以向上跳後向下放置方塊，一次放3個以上的方塊，可能會有窒息的風險或無法放置，這裡不處理。  
11. 不支援復原，蓋錯了就要自己打掉，拆錯了自己建回去，科科科。  

## 實際設計

開發minecraft，想到java；提到java，想到Sun；說到Sun，想到eclipse(誤)。 主要參考minecraft bukkit server的文件[(2)]({{< relref "#reference" >}})，步驟很詳細沒遇上太多問題。  
package name: io.github.yodalee.FastBuild  

照tutorial 的步驟，創建FastBuild class，用FastBuildSetnCmd接受setn command，用hashedMap記錄每一個玩家目前設定的值。  
Event Handler是主要要寫的地方，這裡就要參閱bukkit API的文件，我們這裡要處理的，大部分是在org.bukkit.event.block之下，像放置block的`org.bukkit.event.block.BlockPlaceEvent`，我們就是要處理這個事件。  

```java
@EventHandler
public void onPlace(BlockPlaceEvent event){
}
```
這樣就可以處理這個事件，看看要幹什麼。  
例如BlockPlaceEvent這個class裡面有一個setCancelled的function，用來設定這個event要不要被bukkit處理，如果我們這樣寫  
```java
@EventHandler
public void onPlace(BlockPlaceEvent event){
 event.setCancelled(true);
}
```
那這個server就再也不能蓋東西了ww。 或者可以玩一點更勁爆的  
```java
@EventHandler
public void onPlace(BlockPlaceEvent event) {
  Player player = event.getPlayer();
  Block block = event.getBlockPlaced();
  if (block.getType() == Material.DIAMOND_BLOCK) {
    player.getWorld().strikeLightning(player.getLocation());
  }
}
```
算是某種禁奢條款，只要放置鑽石方塊想炫富就會被雷劈XD。  

回到正題，我們要做的，其實就是從這個place Event裡，取出玩家放置的位子、方位，然後用for loop 重複呼叫placeBlockEvent即可。 目前bukkit好像無法呼叫「在某地放置方塊」的function，因此先用setType來實作，直接取代方塊。  
```java
Player player = event.getPlayer();
Block block = event.getBlockPlaced();
Block againstBlock = event.getBlockAgainst();
BlockFace face = againstBlock.getFace(block);
Block nextBlock = null;
ItemStack stackInHand = event.getItemInHand();
int stackAmount = stackInHand.getAmount();
int n,i;

//get n
if (plugin.playerN.containsKey(player)) {
  n = plugin.playerN.get(player);
} else {
  n = 1;
}
n = Math.min(n, stackAmount);

stackInHand.setAmount(stackInHand.getAmount() -1);
//build
if (face != null) {
  for ( i = 0 ; i < n-1 ; i++) {
    nextBlock = block.getRelative(face);
    if (checkReplaceable(nextBlock)) {
      nextBlock.setType(stackInHand.getType());
      block = nextBlock;
    } else {
      break;
    }
  }
}

// reduce itemStack in hand
if (player.getGameMode() != GameMode.CREATIVE) {
  stackInHand.setAmount(stackInHand.getAmount() - n);
  player.setItemInHand(stackInHand);
}
```
Build大體上的實作就是這樣，其實不算太難。 Break的部分，因為牽扯到手中工具耐久的問題，也許下次再來寫=w=。  

## Demo：
{{< youtube pc9FjvXC7kY >}}

## 原始碼：
本程式公開所有原始碼，歡迎修改後丟pull request，這樣我也不用想break方塊怎麼寫了(誤)  
[FastBuild](https://github.com/lc85301/FastBuild)

## 參考資料 {#reference}

1. [minecraft mod fastbuild](http://www.youtube.com/watch?v=yT5zaBC9O_U)  
2. [bukkit Plugin Tutorial](http://wiki.bukkit.org/Portal:Developers)  
3. [YAML definition](http://wiki.bukkit.org/Plugin\_YAML)
4. [Bukkit API Overview](http://jd.bukkit.org/)，喔這妖受好用的  