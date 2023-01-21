---
title: "自幹世界線變動率探測儀（Nixie Tube Clock）：電路板基礎"
date: 2018-10-23
categories:
- hardware
tags:
- hardware
- NixieClock
series:
- 自幹世界線變動率探測儀(Nixie Tube Clock)
forkme: nixieclock
---

介紹了這麼多，我們終於要進到電路板了，之前介紹的許多東西在這邊一口氣要全部發揮出來，我是沒有很確定輝光管用洞洞板會不會有問題，不過要整合起來還是洗電路板比較潮。  
<!--more-->

## 電路板
電路板 - 也就是 Layout - 這種東西一定要用軟體幫忙輔助，例如小畫家，專業人士跟企業可能會用 [altium](https://www.altium.com/) ，我們沒錢的當然也有沒錢的玩法：
* 開源軟體 [kicad](http://kicad-pcb.org/)
* 網路的電路板軟體 [easyEDA](https://easyeda.com/)（需要註冊，可用 Google 帳號）
* 網路的電路板軟體 [Eagle](https://www.autodesk.com/products/eagle/overview)（需要註冊）

其他兩個都要註冊，真正開源自由使用的其實是 kicad。  

在這裡我是選用 easyEDA 來進行 layout，原因很簡單，因為 easyEDA 允許大家自由分享他們畫的元件跟 layout，我用的輝光管 IN-14 已經有人畫好插孔的 layout，我可以直接引入使用，不像 Kicad 還要自己下載其他人分享的描述檔匯入，方便性上比 Kicad 高一些。  
當然 easyEDA 也是有壞處的，相比 Kicad 它的功能少了不少，像是 DRC，能檢查的只有基本的線寬、線距、鑽孔大小，用 electron 實作的網頁介面，進行一些大量操作的時候速度會明顯慢下來（例如大量元件 lock/unlock 會很明顯的頓一下），我個人的體驗是 Firefox 跑得明顯比 chrome 還要快跟穩www。  

Layout 就請參考[這個連結](http://blog.ittraining.com.tw/2015/11/pcb-layout.html)，裡面有完整介紹 pcb layout 的詳細步驟。  Layout 有兩種可能的設計：放在一塊板子或是把控制板跟插管板分成兩塊，我最後是選擇縮在一塊板子裡面，這樣只要洗一塊比較便宜(yay)，不過相對來說也畫得沒那麼漂亮，從上面看除了輝光管之外還有一堆電子零件會比較醜，其實我不確定能不能兩塊畫在同一塊然後請板廠幫我切開，如果板廠是算面積計價，這樣對他們來說應該也沒差太多才對。  

## easyEDA
下面簡單介紹一下 easyEDA 在 Layout Editor 層的設定，還有跟 Layout 共同的概念，下一章再來提真正的實作，其實這篇我一直在考慮怎麼分成兩篇，畢竟內容太相關了，但合在一章內容好像又太多了：  

### Top/Bottom Layer

走線的部分，分別是正面金屬跟背面金屬，用這兩層畫連線。  
隨著大家對小型化的要求，像我這樣單層、雙層的 layout 已經無法再微縮，市面的產品就有更多層…我查到最多六層的板子，easyEDA 也有支援 4 個 inner layer，不過我們只要雙層板就很夠啦。  

### Top/Bottom Silk Layer

正面文字/背面文字，用來寫字、元件名稱等，通常都是把元件集中在正面，背面文字是不需要用的。  

### Top/Bottom Solder Mask Layer
Solder Mask 是[阻焊層](https://www.researchmfg.com/2017/07/soldermask/)。  
看到 Mask 這個關鍵字城鎮中心的鈴鐺就要噹噹一下，這表示這兩個東西畫的是負片，跟上面幾個正片相反，正片是哪裡畫東西，哪裡有東西；負片是哪裡有畫東西，就表示哪裡沒東西。  
阻焊層應該比較好理解，哪裡有畫東西，哪裡就不會上阻焊層。  

### Top/Bottom Paste Mask Layer

Paste Mask 焊膏防護層。  
焊膏防護層它的目的是要在機器生產的時候貼 SMD 用的，因為我們是手焊所以可以不要管它，這層是在上錫膏的時候，依照這層的負片做成鋼板，把鋼板放在電路板上面之後塗錫膏再移除鋼板，所以造成錫膏層是正片的結果，詳細可以參考[這部影片](https://www.youtube.com/embed/BHVm-fQJPa4)。  

### RatLines：

這個是畫完 schematic 的時候 easyEDA 自動幫你產生的，標示哪個節點要走去哪個節點，理論上再畫完所有走線之後，應該只有 GND 的 Ratlines 會顯示出來；上完鋪銅之後則是完全不會有 RatLines。  

### BoardOutline

標示整個電路板的製造邊界。  

### MultiLayer

在 easyEDA 裡面，有三種不同的孔：Pad, Via 跟 Hole，這幾個有機會用到 MultiLayer。  
相關內容可以參考[工作狂人](https://www.researchmfg.com/2015/06/pth-npth-via/)（這個網站幾乎找 PCB 資料一定會找到，超專業的硬體生達達人），我猜這純粹是用詞不統一的關係，總之他們的關係是這樣的：  
* Hole  
正式名稱是（NPTH，Non Plating Through Hole，非電鍍通孔）：單純的用鑽針在電路板上鑽一個洞，不做任何事，洞裡只有玻璃纖維，上下層亦不導通，事實上 easyEDA 最後鋪銅的時候，會自動繞過 Hole 以免短路，它的用途也就只有鎖銅柱固定電路板。  
* Pad  
可選擇 Top/Bottom/Multi layer，如果選 Top, Bottom 的話就是一塊裸露沒上 solder mask 的金屬，easyEDA 會在 Solder Mask Layer 加上 Pad 的部分，讓這塊最後不上阻焊層；如果是 Multi layer 的話，則是正式名稱的 PTH（Plating Through Hole，電鍍通孔），鑽孔之後會在內部鍍鋼導通上下層，所有 DIP 元件的腳位都是走 Multi Layer 的 Pad，因此焊接只要焊背面，畫走線的時候無論 Top/Bottom 都能導通。  
* Via  
Via 只有 Multi layer 的選項，和 Multilayer Pad 的差別，在於 Via 不會有 solder mask 的對應，也就是說它最後會被 solder mask 的綠漆蓋住，如果是高價位一點板子還會用把 Via 塞起來以免焊錫流進去，因此不能在 Via 焊東西，它只是用來導通電流的。  
如果是多層板，還會有如[埋孔跟盲孔](http://www.researchmfg.com/2011/07/pth-blind-hole-buried-hole/)等東西，不過這已經超出本文的範圍了。  

我們上面提了這麼多，其實 easyEDA 在帶入元件的 footprint 的時候，他就幫我們畫好元件接腳 MultiLayer 的 Pad，只要用上下層金屬把各接點連起來就好，所以真正要編輯的層，其實也就只有 Top/Bottom Layer 連線，打一些 Via 來連接走線，加上 Top/Bottom Silk Layer 的註解；其他包含阻焊層、PTH、NPTH 鑽孔資訊，easyEDA 都會在匯出 Gerber 的時候幫我們處理好，除非有特別設計不然在 easyEDA 上阻焊層是留空就好。  

整個電路板實作的流程大概是這樣：  
1. 依照元件，畫 schematic。
2. 將 schematic 轉成 layout ，代入元件 footprint。
3. 擺位置，各元件放到容易繞線不打架的位子上。
4. 畫走線，鋪銅，上元件之外其他說明文字
5. 列印 layout 檢查，匯出 gerber 檔下線製作

下篇文章就來走一次這個流程吧。 
