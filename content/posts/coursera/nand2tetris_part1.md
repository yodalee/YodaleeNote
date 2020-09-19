---
title: "NAND2Tetris Part1"
date: 2016-07-21
categories:
- coursera
- Nand2Tetris
tags:
- coursera
- Nand2Tetris
- Logic Gate
- ALU
- CPU
- Assembly
- Assembler
series: null
---

五月的時候看到coursera 上了傳說中鼎鼎大名的課程：Nand2Teris，就給它選修下去了。結果後來遇到七月考N1，課程大停擺(yay，最近才慢慢一週週的把課程聽完。  
下面是課程基本資訊：  

|   |   |
|:-|:-|
| 課程名稱 | Build a Modern Computer from First Principles: From Nand to Tetris  |
| 開課學校 | Hebrew University of Jerusalem  |
| 授課教授 | Shimon Schocken & Noam Nisan  |
| 開課時間 | 6 周  |
| 教學方式 | 影片授課  |
| 通過方式 | 每週完成指定的作業，並上傳結果。  |
| 課程網址 |  <https://www.coursera.org/learn/build-a-computer>  |
<!--more-->

## Week 1: 邏輯閘

介紹 Nand 是什麼，如何用 Nand 做出其他邏輯閘，以及課程在Hardware 模擬用的工具和HDL。  

作業要用課程提供的 Hardware Simulator，從Nand堆出其他的邏輯閘。  

這裡說難真的不難，線畫一畫，填個電路就完成了；大部分都是麻煩而已，像是16 路的 Or gate，又沒有像verilog 的 for loop 或 bus 可以用，填接線的數字就飽了（雖然用vim 的block select 可以省一點工夫）  

對應課程：交換電路與邏輯設計。  

## Week 2: ALU

概念講解：用位元表示數字、負數，如何做二進位加法  

這個作業要用上星期作業完成的邏輯閘寫一顆ALU出來，ALU的功能規格是固定的。  
比較煩人的是，它裡面的使用的HDL 跟平常習慣的Verilog 有點差異，導致在寫作業的時候，它一直報錯  
像是它對Bus signal 取值不能在input ，而是在output；同個output 訊號也不能多次使用，這兩個跟verilog 不同。  
例如某個mux output 的 MSB (15)為sign bit，我們需要輸出sign bit；同時要產生zr 訊號，表示output 是否全為零，在verilog 裡會是類似這樣：  
```verilog
Mux16(out=out, a=result, b=notResult, sel=no);
Or16Way(out=nez, in=out);
Not(out=zr, in=nez);
And(out=ng, a=out[15], b=true);
```
課程的 HDL 不行，因為out這個訊號已經當成輸出，不能再接給 Or16Way，同時不能在input 的時候對 out 這個 bus 取它 15 的值  
正確的寫法會是這樣：  
```verilog
Mux16(out=out, out=out2, out[15]=sign, a=result, b=notResult, sel=no);
Or16Way(out=nez, in=out2);
Not(out=zr, in=nez);
And(out=ng, a=sign, b=true);
```
知道這個差別，作業同樣不算太難。  

對應課程：交換電路與邏輯設計。  

## Week 3: Sequential logic

介紹Latch 和Flip-flop 兩個sequential 電路，如此一來我們可以用記錄下來的狀態做什麼？最後的perspective 中有介紹如何用Nand 來實作Latch，D Flip-flop 課程中假定為黑盒子。  

作業的電路模擬器中內建DFF 和DRegister ，要實作Program Counter, Memory 等電路元件。  

RAM 的架構基本上都一樣，寫好最底層的RAM8之後，一路上去的RAM 64, 512, 4K, 16K 都只是複製貼上而已，只是它的Hardward Simulator 怪怪的，有時候會摸擬到 \Explosion/，建議在跑script 的時候可以用慢一點跑.；把 view/animation 選為 No Animation 也或多或少能防止它爆掉。  

Sub bus 用double dot .. 而非Verilog 裡的 comma，同時接線時是接在被 assign 那端，例如要把 15 pins 的 wire 接到元件 16 pins 的input上。  
```verilog
Element(input[0..14] = wire, input[15] = xxx);
```
對應課程：交換電路與邏輯設計。  

## Week 4: 組合語言

上周已經把該有的硬體：ALU，PC，RAM 都寫完了，這周離開硬體，開始介紹 Machine Language 及組合語言(Hack Assemble)，組合語言要如何對應到機器碼，記憶體如何取存用，利用最基本的 memory map 對應到 screen, keyboard 的操作方式。  

這周作業可能比較讓人崩潰，畢竟  

> Unlike other language like Java, machine language is not designed to make people happy.

不過我還是覺得滿輕鬆的啦XDDD  

這周跳脫出來先寫組合語言，下周才會把所有的硬體組起來，寫組合語言等於是知道，機器如何去實習這些功能。  

對應課程：計算機結構。  

## Week 5: 建構一台電腦

介紹電腦整體架構，有這上一週的基礎，我們大致知道電腦會有哪些功能，這周就是要把能夠執行這樣功能的電腦給作出來。  
一些基礎元件：Memory, PC, ALU 第三周都已經實現了，這周只是要把它們放起來，寫出自己的CPU跟電腦。  

要注意的，電路中包含以下的元件：Memory 的 Screen 跟 Keyboard 取用螢幕跟鍵盤、存程式碼的 ROM32K 、以及 CPU 裡的DRegister 和ARegister，這些可以在 builtInChips 裡面找到；要用這些不然硬體模擬器無法抓到這些元件的值。  
如果思考一下，就會發現課程都設計好了，控制訊號就是instruction 逐一填入即可，非常輕鬆；想比較多的反而是何是要讓 PC jump，但基本上線接一接，Mux 輸入的訊號調整一下就會動了。  

對應課程：計算機結構。  

## Week 6: 組譯器

Part 1 最後一周，介紹組譯器  

作業就是寫自幹CPU 的組譯器，什麼語言都可以；為了non-programmer ，課程也設計了手寫作業：人工 assembler 給…呃…有毅力的挑戰者。  
這部分我使用 Rust 來開發，不然我 Rust 都快忘光了，被在台灣謀智隻手撐起 servo project 半邊天的 Rust 台柱呂行大神（又是個好長的稱號XD）屌打，都快無地自容了。  
最後當然是寫出來了，可惜只是作業程度，格式錯掉一點點加個空白就會直接噴射，離工業強度大概還差30 dB，超級容易壞掉，叫它草莓組譯器或者玻璃心組譯器(X，這裡也就不拿出來獻醜了。  

對應課程：計算機結構，編譯器。  

## TL;DR

整體來說的話，因為我本身就是電機背景，硬體跟程式都略懂皮毛，寫作業輕鬆愉快，聽課也像在複習忘掉的東西XD  
如果沒有相關背景的話也許會困難一點，但修完的那刻，真能領略電腦這複雜又簡明的發明。  
能這樣從Nand 往上一路打造出電腦也是很有趣。整體作業非常精巧，沒有多餘的浪費，week 1打造的邏輯閘，在week 2 ALU 、week 3 PC、week 5 CPU 都會用到，不需要特別打造自訂的邏輯閘，一步步照著說明也能自幹一台電腦出來，可以想見規劃這門課程的時候，是真的經過千錘百鍊的設計。  

修完這門課，以後看到電腦，儘管它做了那麼多事，接了除了課程沒提到的各種周邊，我們還是可以說：「假的！不過只是相關概念延伸罷了，嚇不倒我滴」  

啊不過寫到這就覺得我只不過在小打小鬧，真強者我同學都是跳下去改變世界，哪像我還在這裡聽課程QQQQ 