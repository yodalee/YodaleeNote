---
title: "數位電路之後，verilog 系列文1：談談 verilog 三大塊的架構"
date: 2012-06-30
categories:
- verilog
tags:
- verilog
series:
- 數位電路之後，Verilog 系列文
---

常說「寫verilog一定要有硬體的思維」，這是因為verilog，亦或VHDL的用意，最終都是要轉成硬體上的 register 和 combination circuit，
我自己的寫verilog比較不像在寫一般的程式語言，可以宣告各個變數、作運算，然後輸出結果；
verilog會不斷宣告module、register跟combinational circuit與其中的接線，結合成一個完整的電路。  
<!--more-->

總的來說，我認為verilog對語法結構的要求更為嚴格，每寫一行code都會對應生成一塊硬體，如果code結構不好，生成的硬體架構也會很糟，
我認為大多數的書跟講義，都沒有強調這點，大多花了很多篇幅先介紹各種combinational circuit的寫法，把語法結構的內容放在FSM的範例裡，
很像在教物件導向的語言，卻不先教物件的概念一樣，套句黃猿的口頭禪：「真奇怪呢~」。  
依照個人寫verilog的經驗，統整成個人所謂的「三大塊的架構」，在這第一篇中分享給大家，希望大家都能有效掌握三大塊架構的威力，輕鬆寫出「行為和預期中的相同的電路」。  

從下面我會先介紹一些電路設計時的基本硬體，verilog如何轉換成這些硬體，最後再來講，FSM的概念和三大塊架構的語法。  

## 基本硬體：  
上過基本電路設計的都會知道，電路元件分成兩大類：combinational circuit和sequential circuit。
* combinational circuit就是不斷的進行運算，輸出只和輸入有關
* sequential circuit則會輸出則會看輸入以及當前電路的狀態

但以當前數位電路的情況，其實可以說，sequential circuit大多都是由D-flip flop作為register所組成，特色在於，D flip-flop每遇到clock跳動就會把輸入點的資料記錄下來，待下一次clock跳動。  
拿一個城市的交通作比喻：  
* Combinational circuit就像馬路，負責讓車(信號)流動，改變車道(運算)  
* Sequential circuit則像紅綠燈，負責管理信號什麼時候可以通行，到下一個combinational circuit。  

就如下最經典的電路架構圖所示：  

![canonical](/images/verilog/canonical.png)
上方的D-flip flop在clock來時記錄combinational 的輸出，combinational circuit則靠register的記錄值與輸入信號，計算輸出與下個記錄值。    

## verilog的轉換
為了要對應combinational 和sequential 兩種電路，verilog裡面兩種不同的宣告方式：  
```verilog
// edge trigger
always @( posedge/negedge clock)
// level trigger(感謝為中大神指正)
always @( state, counter)
```

前者會合成出：由D flip flop的register架構，由括號中的接線作為register的觸發信號，把資料寫入某個register當中，如：`state <= state_next`。  
就會在clock跳動時，將`state_next`的資料，寫進state的register裡。記得在實驗中討論時，我都管這個叫「敲clock」，因為感覺很像在clock來的時候，就把資料敲進register裡面XD。  

後者則會合成出：純粹的combinational circuit，以括號中的訊號為輸入訊號，執行其中的邏輯設計；
所以說，這樣的寫法中，所有有用來assign值的信號(RHS)，都要加到括號裡面，也就是sensitivity list，如下面的counter：  
```verilog
always @(state, counter)
begin
  counter_next = counter;
end
```
因為總要有這個信號當輸入，才能用它來給其他信號值，現在也可以用always @(*)來代替，讓compiler自動宣告為輸入。  

## FSM與三大塊的架構介紹
現在我們明白了combinational circuit和sequential circuit的關係後，就可以看一下有限狀態機FSM的概念。  
有限狀態機其實是一個很常用的model，用來描述整個電路面對不同輸入(需求)時，該有什麼樣的變化和行為，無論要寫什麼樣的電路，
個人還是會先在紙上構思完FSM的架構，再由FSM下去寫，架構就會很清楚。  
下圖是一個很簡單的FSM的模型，用來描述：  

![FSM](/images/verilog/FSM.png)
呃…一個2 bits的counter，數到三的時候輸出是1，這是很簡單的FSM。  
FSM最重要的有幾個元素：**狀態、輸入、輸出**。  
隨不同的輸入，會跳到不同的狀態；輸出可以只和狀態有關(Moore machine如上圖)，也可以和狀態、輸入都有關(Mealy machine)。  

其實，從FSM上面，已經能看出所謂的三大塊架構，那就是：  
1. State register: 把狀態的寫入，透過clock控制的register，把next state隨clock寫入state的register中。  
2. Next state logic：計算下一個狀態，根據目前的input和state，運算下一個next state。  
3. Output logic：輸出，根據目前的狀態(或輸入)，運算當前輸出。  

相對應的，也就是三大塊的架構：  
1. 含posedge的always block，將變數的next state寫入register。  
2. 不含posedge的always block，當中運算各個next state。  
3. 不含posedge的always block，當中只負責其他數值運算。  

實際對應的code就是：  
```verilog
//state register
always @(posedge clock)
begin
  State <= state_next;
end
```
注意，只有這裡可以用posedge clock，因為只有這裡宣告所有register。  

```verilog
//next state logic
always @(*)
begin
  if (input == 1'b1)
    State_next = state+1'b1;
  else
    state_next = state;
end
```
這裡寫下一個要敲進register的值的運算  

```verilog
//output logic
always @(*)
begin
  output = (state == 2'd3) ? 1'b1:1'b0;
end
```
這裡寫輸出的function。  

通常我會每個不同的變數，都有一個獨立的always block，如下面的state跟counter：  
```verilog
//state register
//state
always @(posedge clock) begin  state <= state_next;   end
//counter
always @(posedge clock) begin  counter <= counter_next;   end

//next state logic
//state
always @(*) begin
    if (counter  == 2'd10) state_next = state+1'b1;
    else state_next = state;
end
//counter
always @(*) begin
    if (input  == 1'b1) counter_next = counter+1'b1;
    else counter_next = counter;
end
```
如此一來，每個變數的logic都很獨立，各自受誰影響也可以一目了然，要改變數的行為時，只要搜尋該變數名，就可以快速跳到該修改的地方；這在變數多的時候，修改起來會變得很輕鬆。  

## 其他相關的內容整理
1..看看各種verilog語法是如何合成基層的電路。  
<http://eesun.free.fr/DOC/VERILOG/synvlg.html>  
2..OO無雙部落格，對FSM寫法的描述，相當完整，推薦花時間讀完。  
[http://www.cnblogs.com/oomusou/archive/2011/06/05/fsm\_coding\_style.html](http://www.cnblogs.com/oomusou/archive/2011/06/05/fsm_coding_style.html)  
