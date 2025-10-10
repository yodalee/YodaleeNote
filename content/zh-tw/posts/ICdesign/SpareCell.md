---
title: "ECO cell 與 Spare Cell"
date: 2025-09-10
categories:
- ICdesign
tags:
- ICdesign
---

這篇跟之前的 DFT 一樣，介紹一下 ECO 這個我還沒完全嘗試過的東西，我們在設計上要怎麼支援 ECO
，以及 Spare Cell 這個最常用在 Layout 上的 ECO 解決方案。

<!--more-->

當你做的晶片來到產品等級，有可能就要考慮一下 ECO 的問題。  
ECO 的全名是 Engineering Change Order，ECO 可參考以下文章：[芯片设计中的ECO是什么？](https://cloud.tencent.com/developer/article/1892478)。  
如果要我一言以敝之，所謂 ECO 就是發現了設計上的問題，由於正規流程已經走完，在時間表內無法使用正規作法，
因此改用工程方式強行處理掉問題，就像[紐約那棟意外發現可能會被風吹倒的大樓焊上鐵板](
  https://www.youtube.com/watch?v=Q56PMJbCFXQ)讓它安全的例子。

上文中三階段的 ECO 仍然遵循設計原理：
> 愈早發現的問題，修正成本愈低

本文介紹的 ECO/spare cell 就是修正成本最高的那種，生產的時候，可以先由晶圓廠完成晶片的邏輯閘，
小部分做完後續流程進行測試，其他大部分的金屬層則等測試完成，確定不用 ECO 後再繼續做。  
如果測試發現問題，就能修改光罩改變金屬層的走線來修改實作的邏輯。

# ECO cell

首先是 ECO cell，可以想像是一種特殊的 standard cell，由晶圓廠提供，可以透過微幅的修正來改裝成各種邏輯 cell。  
首先 ECO cell 並不是所有晶圓廠都有提供，事實上*我活到現在也還沒看過 ECO cell 長什麼樣子*，
找了一下儘管有如下的參考資料，內容也多殘缺不全：
* [Metal ECO implementation using Mask Programmable cells](https://www.design-reuse.com/article/60791-metal-eco-implementation-using-mask-programmable-cells/)
* [Metal Configurable Gate Array in Metal-Only ECO](https://www.nandigits.com/gof_display_doc.php?document_type=gate_array)

大致參考一下應該可以看懂它是怎麼做到的。

# Spare Cell

既然 ECO cell 不是人人都提供，那麼還有另一種實現 ECO 的方式，就是用 layout 
上剩餘的空間，多塞一些備用的邏輯閘，等到需要 ECO 的時候，再把接線轉去備用的邏輯即可。  
這些 cell 的輸入要綁定到 0 Ground 或 1 VDD，輸出則是空接，讓它們的耗電可以降到最低。

至於要加入哪些邏輯閘，就看各公司內訂了，理論上在你公司裡找一找，應該能找到前輩留下來的設定
~~沒有的話就塊陶啊~~，我自己的建議如下：
* 一般邏輯閘一個，接線少如 NAND, Mux, Inverter 等給兩個到五個
* D flipflop 給兩個，用得有點像 FPGA 的 Slice 一樣
* BUF 兩個
* 不同 size 的 Delay Cell 都放一個
* TieHi TieLo 各放一個，服務整個 Spare Module

下面是一個 INNOVUS tcl 的範例，求簡單邏輯閘只放 NAND，請**記得 cells 要改不要直接抄**，基本語法就是：
* -cells：有什麼 cell 跟要放幾顆
* -tie_low：cell:pin 指定哪些 pin 要接地
* -tieoffs：tie high/low 是哪個 cell

```tcl
create_spare_module -module_name SPARE_module -cells \
  NAND 10 \
  DFF 2 \
  BUF1 2 BUF2 2 \
  DLY_1 1 DLY_2 1 \
  TIEHI 1 TIELO 1 \
-tie_low { \
  NAND2:A \
  DFF:D \
  BUF_1:A BUF_2:A \
  DLY_1:A DLY_2:A } \
-tieoffs {TIEHI TIELO}
```

## SPARE 的面積

插入的步驟，一般在 place 前後就要完成插入，若是到了 routing 完再來插 spare cell，會導致嚴重的 timing issue。  
在插入 Spare cell 的時候，會力求儘量灑得平均，在未來 ECO 的時候才能就近找到可替換的邏輯閘。  
數量參考這篇[后端P&R加入spare cell](https://blog.eetop.cn/blog-1592-6947123.html) 
是建議整體設計面積的 3%-4%，並不算小。  

至於要如何計算 SPARE size，首先會先用 get_db 取得**已經 place 完的** spare instance，並限制到其中的一個
```tcl
get_db insts -if ".name == *SPARE*"
get_db insts -if ".name == *SPARE_spr_1/*"
```

使用這篇[Command to get cell Area](https://community.cadence.com/cadence_technology_forums/f/digital-implementation/20572/command-to-get-cell-area) 
的 tcl script，將 module 內的 cell area 加總，得到一個 module 的 area。

```tcl
set area 0
foreach inst [get_db insts -if ".name == *SPARE_spr_1/*"] {
  set cell [get_cells $inst]
  puts "[get_property $cell ref_lib_cell_name]"
  set area [expr $area  + [get_property $cell area]]
}
puts "Total Cell Area: $area"
```

**ref_lib_cell_name** 這個 property 是把上面 get_cells $inst 的其中一個撈出拿出來，用 report_property 得到的：
```tcl
report_property [get_cells xxx]
```

## 插入 Spare Cell

innovus 在插入 SPARE_module 的時候，到底怎麼插比較好？

第一種嘗試：
1. 先插入 spare cell
2. 執行
```tcl
set_spare_insts -insts "*SPARE*"
set_db place_global_module_aware_spare true
```
3. 執行 place_opt_design

結果沒太平均，很多 SPARE cell 被放到角落去了，嘗試後比較平均要這樣做：

1. `place_opt_design` 先把設計擺放上去
2. 擺放 spare cell，不要讓 innovus 自己擺，改用下列指令指定 step 要多少：
```tcl
place_spare_modules -prefix SPARE -module_name SPARE_module
  -offset_x 50 -offset_y 50 -step_x 200 -step_y 200
```
要擺放多少請自己算，例如我的晶片尺寸如果是 1000x1000，上述的就會把中心放置在 50,250,450,650,850 
共五組，二維就會放上 25 組，搭配面積計算插入的量是否符合所需。  

3. 最後再進行一次 place_opt_design，讓它依照目前的密度、繞線擁擠程度調整一下

由於 opt 的邏輯是儘量尊重原有的擺放，移動得愈少愈好，就能得到一個比較好的結果。

# ECO cell 與 Spare cell 比較

以上兩種 ECO 的解決方案，各有什麼優缺點呢？

第一個層面是兩者的改動成本，也就是光罩。  
Spare Cell 的優處是在 ECO 的時候，改變 Metal 層的光罩即可，本來 cell 製作的光罩都沒有動。  
ECO cell 的話，由於它的改動是去改變一個 cell 內的接線，因此會需要動到 Contact
，以及上方的 Metal layer，多一層要改的光罩就是多一層成本。

在設計方面，ECO Cell 較為簡單，只要填入單一種 ECO cell 即可；
Spare Cell 則只能插入固定種類的 cell，NAND 就是 NAND，那如果這次 ECO 需要很多的 XOR 呢？  
ECO cell 能全部重新修改為 XOR cell，彈性較高，Spare cell 可能就力有末逮了。

另外上述參考資料的 ECO cells 在 ECO 時能串聯更多 ECO cells 來增加輸出的推力，而 spare cell 
插入的都是最小的邏輯閘，推動力相對小很多，可能在 ECO 後出現 DRVs 問題。  

只能說兩者各有優缺點，請自行判斷了。

# 如何在 INNOVUS 中進行 ECO

等我遇到了我再來完成這一章