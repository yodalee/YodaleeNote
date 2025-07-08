---
title: "  自幹世界線變動率探測儀（Nixie Tube Clock）：電路板實作"
date: 2018-10-25
categories:
- hardware
tags:
- hardware
- NixieClock
series:
- 自幹世界線變動率探測儀(Nixie Tube Clock)
forkme: nixieclock
---

下面就真的要開始用 easyEDA 畫 Layout 了。  
EasyEDA 能做簡單的模擬，不過基本上功能非常的弱，只能模擬一些節點的電壓，大部分的元件也沒有模型可供模擬，所以請放棄在 easyEDA 模擬的念頭。  
<!--more-->

## 第一步：畫 schematic，調整 footprint

是在 easyEDA 上面畫 schematic ，如前幾篇文章出現的高壓電路的 schematic；在畫 schematic 的時候，就可以想想 Layout 大概要用什麼元件，簡單的元件如電阻、電容、電感、二極體等等會出現在左邊的選單裡，並且可以選擇所要的型號，像電阻就有 0201, 0402等平面元件跟插件 Axial 0.3-1.2 等 16 種可選。  
比較複雜的元件可以從上面的選單 Place -> Component，打入關鍵字，插入找到的元件，通常同一個元件都能搜尋到 SMD 跟 DIP 兩種版本，記得要插入正確的；插入元件之後要取一個好的名字，方便在 Layout 跟焊接的時候，能夠快速知道是哪一個元件。  
![eleement](/images/nixie/selectelement.png)
編輯中也能在上面的選單找到 Footprint Manager，裡面可以編輯每一個元件對應的 footprint，還有元件符號跟 footprint 腳位的對應，來跟真實元件對應；例如不知道為什麼，我買到一批 5050 RGB LED，腳位跟預設的腳位就是不一樣，因此用 footprint manager 調整過；另外像是0603的電阻因為預設的 footprint 有一個 silk 框，我想畫得密集一點就換了個沒有 silk 的 footprint。  
![footprint](/images/nixie/footprintmanager.png)
建議上每畫一個區塊的 schematic ，就定時按一下 Update to PCB，讓 easyEDA 把 schematic 上的元件放到 PCB 上，然後安排一下 layout footprint 的位置；因為如果等畫完再一次轉換，會造成所有的 footprint 都擠在一起，讓你分不出誰是誰，一次轉一些安排位置，或至少分個群，之後在 layout 會方便很多。  

## 第二步：擺放 footprint

在 Layout Editor 上面畫 PCB，進到 Layout Editor 之後，首先先設定 Design Rule 跟網格等資料。  
網格可以用 mm 或是 mil 當單位（用 inch 當單位是有一點太大了），easyEDA 預設是用 mil 當單位，如果要用 mm 當單位的話記得一定要把 grid size / snap size 從 0.254 mm 換成比較好看的數字，如 0.1mm  
Design Rule 請參考廠商給的資料，例如下面是我選用的 [JetPCB 的製程資料](http://tw.jetpcb.com/Cht/Document/PCB%E8%A3%BD%E4%BD%9C%E8%A6%8F%E7%AF%84.pdf)；easyEDA 畢竟是免費軟體，提供的規則檢查只有線寬、線距、鑽孔大小、線長；不像 kicad 除了這些，還能做更多的像是各層獨立規則。  
只截取 DRC 部分的規範：  

* 線寬 0.25 mm
* 線距 0.25 mm
* Via 直徑 0.5mm
* Via 鑽孔直徑 0.3mm

畫好 schematic 之後，Layout Editor 上面應該已經有所有元件的 footprint，先做好放好位置、調整方位等，如果看到有 footprint 不是自己想要的，也可以隨時回 schematic 修改然後再 update。  
個人經驗是，因為 easyEDA 功能不全的關係，一但畫了走線之後如果又修改 footprint 的腳位對應，要再改走線就非常費工，所以畫走線之前，一定要確認好 footprint 腳位跟 schematic 都已經是正確的。  

## 第三步：畫 Layout 走線

放好位置之後就能開始畫走線，雖然 easyEDA 有提供 [auto router](https://docs.easyeda.com/en/PCB/Route/index.html)，但我個人不建議使用，它只會儘量畫最短路徑畫，反而沒什麼規則，例如我的輝光管部分，因為輝光管的陰極同數字是全部接在一起的，它就真的給我照最短路徑畫得亂七八糟。  
不過 auto router 也可以當一個指標，如果你的 layout 開了 auto router 跑不到 90% 以上，表示你的 layout 還不夠簡單，可以看看 auto router 都是哪裡繞不出來一直在重試；簡而言之：easyEDA 的 AutoRouter 只會繞出一堆垃圾，請還是乖乖用手畫。  

在 easyEDA 裡面用 track 畫走線，照著 ratlines 用走線連起來就行了，在輝光管部分的畫線要點在於分開上下板，我是下板走垂直線、上板走水平線，這樣子上下板的線就不會打架，如下圖所示：  
![wire](/images/nixie/wiring.png)
另外有一些其他 layout 的注意事項：  

* 為了燒錄，要把 5V, GND, TX, RX, Reset 拉出來
* 用個 jumper 隔離外接 5V 跟 78M05 的輸出，這樣可以單獨測試所有控制電路的功能。
* 這個是我做的時候沒想到的，在通往 LED 的 5V 電源線上加上 jumper ，這樣覺得 LED 太亮的時候，可以用硬體的方式關掉 LED。
* 電阻、電容、LED 可以的話儘量選 0603 省空間，我覺得 0603 是覺得可以輕鬆焊的極限，0402 或更小就很抖了。
* 在 MC34063 那邊的限流電阻，因為在最大電流下，功率可能會升到 100 多 mW，所以我是用 1206 的電阻；我也是現在才知道原來電阻的尺寸是跟它能[承受的功率](http://www.resistorguide.com/resistor-sizes-and-packages/)有關。
* 高壓電路的地方，依這個論壇所言，讓電感與二極體還有MOS位置最短。
* 所有的晶片，在 VCC 的接點前都保留一個 0603 約 100n 的電容做為穩壓。
* 依照晶體振盪器 datasheet 的建議，在振盪器周圍一個範圍要鋪地，避免信號線出現，以免影響時脈的準度。

JetPCB 也有提供一些[參考規範](http://tw.jetpcb.com/Cht/Document/%E9%9B%B6%E4%BB%B6%E4%BD%88%E7%BD%AE%E6%B3%A8%E6%84%8F%E4%BA%8B%E9%A0%85.pdf)，我大致整理一下這次畫 Layout 的規則：  

* 電源線寬為︰1 mm - 1.2 mm，如果有更大電流的應用，請參考[線寬計算機](http://circuitcalculator.com/wordpress/2006/01/31/pcb-trace-width-calculator/)。
* 信號線寬建議為︰0.2-0.3 mm，我是用 0.4 mm；其實 PCB 承受電流的能力很大，1oz 的銅、0.25 mm 差不多就能走 1A 了，所以畫細一點是沒差的。
* Via 有兩種，外徑/內徑為 1mm/0.5mm 跟 1.6mm/1mm ，分別用在訊號線跟電源線的 via。
* 鋪銅間距：因為我們的電路板會走高壓電，在網路上找到一款[間距計算機](https://www.smps.us/pcbtracespacing.html)，我們最高的電壓應該是200 伏特，算出來的安全間距是0.4 mm ，因此我是用 0.6 mm 作為鋪銅間距。

## 第四步：鋪銅與 DRC, LVS 與他

Layout Editor 左邊的 Design Manager 打開，裡面有三個選項：Components，Nets 跟 DRC Errors  
Component 方便你找元件用，比較沒這麼重要；Nets 跟 DRC Errors 分別是 LVS 跟 DRC；完成走線的時候， Nets 裡面應該只有 GND 是錯誤的，因為我們還沒有鋪銅，把整個地連起來。  
鋪銅選擇工具的 Copper Area，把要鋪銅的部分框起來，easyEDA 就會自動完成鋪鋼，正反兩面都需要鋪銅，鋪完之後再從工具列選 Copper Area Manager 去調整鋪銅間距。  
鋪完銅的時候，LVS 就要可以通過了；DRC 的話在鋪銅前跟鋪銅後都要跑過一次，第一次是要修掉走線的錯誤，第二次的是要確認整個 layout 沒有問題，畫完大概會像這樣：  
上板走線：  
![top](/images/nixie/top.png)
下板走線：  
![bottom](/images/nixie/bottom.png)
上下板走線：  
![topbottom](/images/nixie/topbottom.png)
基本上我是畫的超寬鬆的，寬度因為受限於輝光管比較難縮，高度其實可以再縮一點，元件排更密一點，我覺得縮 1-2 cm 不是問題，不過第一次畫 layout 自然是小心為上。  
個人經驗是不要讓焊點間的距離小於 0.7 mm 左右，再小第一個焊的時候容易短路，烙鐵也可能不小心戳到不該戳的地方。  

## 第五步：收尾下單

做完這些，就可以匯出 layout 成 Gerber 檔下單製造了，最後還有一些，像是留下未來打銅柱的鑽孔，留一些文字等等。  
在真正下單之前一定要再次檢查，把 Top Layer 跟 Bottom Layer 匯出成 pdf，用印表機 1:1 分別印出，對照有沒有哪裡有問題，手邊買好的元件是否能正確的對到印出來的穿孔，畢竟板子做了就是做了，做壞要用暴力修的難度也很高，多檢查幾次不吃虧，我就有對照的時候發現 schematic 的地方有畫錯，差點整塊板子變廢物，Board is dead, mismatch。  
洗板選用戀戀科技 Marten 大大推薦的 [JetPCB](http://tw.jetpcb.com/)，好到連[日本人都來用](http://www.narimatsu.net/blog/?p=8826)？（雖然說他們的問答版上，有一個回答就是不服務台灣以外的顧客owo），不過他們的網站需要先註冊為會員才能下線。  

easyEDA 下載好的 gerber 檔，裡面的 PasteMask 可以直接刪掉沒關係，其他的打包送給 JetPCB，工程人員會再次幫你檢查電路板，看看有沒有太大的問題，我是選三天到貨的方案， 電路板尺寸 264 mm X 104 mm，總價是 4200 NTD。  
可…可惡，早知道當年在學校的時候就該來做 nixie clock，在學校就能用學校的洗板機免費自己洗驗證板了，現在都要花大錢去外面洗板子，畫錯錢就直接噴飛QQQQ。  

總之電路板最後終於成功下線，之後就是靜待三天，等電路板寄到就可以開始焊電路啦。
