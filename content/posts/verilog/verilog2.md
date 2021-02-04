---
title: "數位電路之後，verilog系列文2：常見的 verilog 譔寫錯誤"
date: 2012-07-04
categories:
- verilog
tags:
- verilog
series:
- 數位電路之後，Verilog 系列文
---

感謝鄭為中大神的提醒，要寫這篇verilog常見錯誤文，也感謝鄭為中大神對我 verilog 觀念的澄清：)  

譔寫verilog最常見的錯誤，當然就是~~syntax error~~……= =  
當然這裡不討論這些，雖然他們很常出現，像忘了加分號、拼錯字之類的，我們延續上一篇對verilog結構的討論，再來看看，寫得不好的verilog code會造成怎麼樣硬體上的後果，與上一篇結構問題相同，需要轉成硬體的結果造成這個verilog獨有的錯誤。  
<!--more-->

這篇討論使用Altera Quartus II編譯時，兩種常見的錯誤： **產生 latch** 和 **產生combinational loop**。  

## 產生latch
產生Latch最主要的原因是沒有把所有條件寫乾淨。  
我們考慮電路合成的情形，當我們寫一個if，或者case，這些東西在電路內都會轉成mux，例如以下的code：  
```verilog
if(in=1) begin
  counter_next = counter +1;
end
else
begin
  counter_next = counter;
end
```
這會變成下面的電路(好醜的multiplexer…..)：  
![combinational](/images/verilog/combinational.png)

如果是case，就是多對一的mux。  
例如常見的七段顯示器的code，輸入一個數，轉成相對應7個光點的輸出，這個大概就會合成類似，16對1的mux：  
```verilog
case(digit)
   4'd0: segment_out = 7'b1000000; // 1 -> dark 0 -> light
   4'd1: segment_out = 7'b1111001;//      ___a___
   4'd2: segment_out = 7'b0100100;//    |       |
   4'd3: segment_out = 7'b0110000;//   f|       |b
   4'd4: segment_out = 7'b0011001;//    |       |
   4'd5: segment_out = 7'b0010010;//    |_______|
   4'd6: segment_out = 7'b0000010;//    |   g   |
   4'd7: segment_out = 7'b1111000;//   e|       |c
   4'd8: segment_out = 7'b0000000;//    |       |
   4'd9: segment_out = 7'b0010000;//    |_______|
   default: segment_out = 7'b1111111;//      d
endcase
```
注意到，上面無論是if還是case，最後都有一個else/default，再次重申，verilog和一般的C是不一樣的，在C裡面的if 就是判斷條件，符合就跳到指定的程式碼，不符合就繼續執行；但verilog是要轉成電路的，你不指定else，mux的輸入要接給誰？  
一般verilog的編譯器會指給輸出，也就是如下的電路：  
![latch](/images/verilog/latch.png)
如此有個訊號被鎖在這個mux裡面，就是基本的latch，雖然一般來說，這樣的latch對電路的行為影響不算太大，有時候充滿latch的code還是可以正常運作；但個人習慣上還是強烈建議把if, case全都加上else，消掉所有的latch；因為有latch 的code的行為較難預料，輸出變得依據"上一個狀態"來決定，而不是單純的combinational circuilt。  

## Combinational loop
另一個情況是產生combinational loop。  
理論上，用我上一篇所說的FSM和三大塊架構下去寫，是不會出現combinational loop的，三大塊的架構最主要的核心，就是把"變數" (state)和"變數的下一個狀態"(stata\_next)的運算分開，在combinational 的部分就只靠state(和其他變數)去運算state\_next。  
所以說，在verilog 裡面，絕對絕對絕對沒有assign的左右兩邊是相同的狀況，這也是verilog最難讓人習慣的地方，因為一般程式寫a=a+1實在太常見了。  
比如說  
```verilog
always @(*) begin
    state = (counter=2’d2)?state+1’b1:state;
end
```
這樣的code是絕對不可以出現的狀況，會產生另一個常見的 combinational loop 的警告。有時候這樣的 code 也可以存活，但出現 combinational loop 一般都會大大加重 quartus 編譯時的負擔。  
quartus 會針對電路去做很多的模擬，確認電路工作沒有異常，造成編譯效率的下降，曾經遇過充滿 combinational loop 的 code，編一次耗時40分鐘，修掉之後卻只需要10分鐘，影響之大由此可見

寫 verilog 時，養成良好的習慣，把**會受到自己狀態，而影響到下個狀態的變數，都產生兩組**，X，跟X\_next，才不會把自己搞得暈頭轉向。  

