---
title: "數位電路之後，verilog系列文3：寫一個module"
date: 2012-07-06
categories:
- verilog
tags:
- verilog
series:
- 數位電路之後，Verilog 系列文
---

在上一篇裡面，我們談過了verilog 三大塊的寫法，以及常見的verilog錯誤，那現在就來看看，一個verilog module的構成，  
其實一個module，就好像在寫一個完整的電路，有哪些input, output，要有多少個register，之間的接線，甚至要包住其他的module，是一塊很完整的block。  
<!--more-->
下面是我在vim裡預設的module格式，大家可以參考，不過我覺得其實這部分每個人都有每個人的風格，有人覺得parameter的部分應該提到module之外，因為那些其實不是電路本體的部分，而是在編譯器編譯時就把code裡的變數代換掉了，所以最重要的還是自己習慣就好：)  
```verilog
module /*module name*/(
/*parameter*/
);

/*================================================================*
 * PARAMETER declarations
 *================================================================*/
/*================================================================*
 * REG/WIRE declarations
 *================================================================*/
/*================================================================* 
 * Module 
 *================================================================*/          
/*================================================================* 
 * Combinational circuit 
 *================================================================*/          
always @(*)begin
end  
/*================================================================*
 * Sequential circuit
 *================================================================*/ 
always @(posedge clk or negedge n_rst) begin
end 
/*================================================================* 
 * Output circuit
 *================================================================*/ 
always @(*)begin
end  
    
endmodule
```

## inout宣告，行1~3：  
第一行宣告module 名字就不用說了。  
從第二行開始是input與output的宣告，其實這好像也沒什麼好說的，就直接宣告各個input 與output：  
```verilog
input clk_50M,  
```
有兩點可以注意的是：  
第一在 top module，input 與 output 的名字，最好能和原廠提供的 pin assignment 的 qsf 檔或是 xls 檔相對應，才能大量節省 pin assignment 的時間。  
記得剛開始實驗時，都會把input, output名字取得比較好記，像送給七段顯示器的秒數資料，我就叫second1, second2這樣，當然pin assignment 的時候就要一個一個去對照pdf 檔，把名字對應起來，這樣當然很智障= =。  
好的做法是，取名就跟pin assignment一樣，如果覺得名字實在太鳥了，下面再用assign的方式，承接input的值或是對output給值。  
當然也可以直接去改pin assignment的檔案，不過何苦呢XD？  

第二點是註記：  
如果是top module，因為input output是來自於開發板上的各元件，通常就依照元件分群；如果是其他的module，則依信號給的對象分群  
例如現在寫了一個「輸入為4bits的數，輸出為七段顯示器的信號」則我會這樣註記，把對象分開：  
```verilog
//main
input clk,
input [3:0] number,
//seven segment
output [6:0] segment_signal
```

## Parameter 和reg, wire，行5~10：  
這個好像真的沒什麼好講的…  
大概只有wire，如果是一個行為很簡單的wire，例如要連接到inout的輸出：  
wire sram\_data = (state == STATE\_WRITE)? data\_in\_buf : 16'bz;  就可以直接補完。  

## Module，行11~13：  
就連接module嘛 = =，好像也沒什麼好講的。  

## 電路設計，行14~28：  
這裡包括了next state logic, sequential block, output logic，其實不一定每一塊都要有，看電路的設計。  
據我強者同學phoning表示，DSD的建議是，next state logic跟output logic寫在一起，不過我習慣還是會分開寫；但我的確有在想，把sequential block的部分移到電路最後，因為這個部分通常是最不常改到的地方，我想這也是一樣，大家習慣就好。  

我倒覺得這裡正好講一下reset的觀念，也就是 code 裡的 n\_rst：  
在verilog裡面，因為寫的是電路，當電路通電的那一瞬間，所有register裡面的值都是亂七八糟的，而不是像c code，可以在宣告時寫int a=1，它就是1；偏偏這時候，verilog又用一個很容易誤會的關鍵字：initial。  
所以就很常有人以為，只要寫：  
```verilog
initial begin State <= 0; end
```
就可以讓reg回到原來值…(其實這部分個人不確定，因為這樣寫過，而且好像還真的能用)  

比較正確的作法是：用一個開關之類的為reset信號  
然後在sequential電路的部分都加上  
```verilog
if(~n_rst)begin     //要negedge reset或posedge reset隨你高興啦……
    state<=0;
end
else …………其他的內容
```
這樣一但發出reset 信號，所有的register都會清成起始值了。  

## 註解：  
這個在prototype上面沒有，我也是最近才學到的，在寫完module，別忘了加上instance，把這個module該如何引用寫在最前面，方便其他人的引用啊，如下所示：  
```verilog
/* instance
module_name(
// front comment
.port1(), // back comment
.port2(),
.port3()
);
*/
```