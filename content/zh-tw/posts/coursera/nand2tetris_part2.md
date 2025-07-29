---
title: "NAND2Tetris Part2"
date: 2017-05-01
categories:
- coursera
- Nand2Tetris
tags:
- coursera
- Nand2Tetris
- Jack language
- assembly
- compiler
- stack machine
- operating system
series: null
---

三月時看到coursera 上，Nand2Teris 第二部分終於開課了，同樣給它選修下去；最近剛把最後的 project 寫完，完成這門課程。  
課程基本資訊：  

|   |   |
|:-|:-|
| 課程名稱 | Build a Modern Computer from First Principles: Nand to Tetris Part II |
| 開課學校 | Hebrew University of Jerusalem |
| 授課教授 | Shimon Schocken & Noam Nisan |
| 開課時間 | 6 周  |
| 教學方式 | 影片授課  |
| 通過方式 | 每週完成指定的作業，並上傳結果。  |
| 課程網址 |  <https://www.coursera.org/learn/nand2tetris2>  |
<!--more-->

Nand2Tetris 2 的影片長度明顯比 season 1 長得多，光第一週的影片，要介紹 Virtual Machine 概念，又要講解整個 memory layout, pointer access 的概念，第一週影片長達200 分鐘，還不算上 week 0 複習 Nand2Tetris 1 Machine Language 的部分。  
另外 part 2 畢竟進到軟體的部分，作業都很吃軟體能力，像是實作 VMTranslator，編譯器，寫高階語言，也不像第一部分，有提供手爆作業給不會寫程式的人，如果沒有基本程式能力選修起來會有些難度。  
作業我本來想延續上一個 part 1 都用rust 寫作業，後來…還是偷懶改用Python 寫了(yay，我魯我廢我不會寫 rust QQQQ。  

讓我們帶過七週的課程內容：  

## week 1 Stack machine

介紹整體 Nand2Tetris stack machine 的架構，整個 Nand2Tetris 都是執行在這種stack machine 上面，之所以用 stack machine 應該是因為相較 register machine，stack machine 還是好做一些，Memory 設定為：  

|memory address | purpose     |
|:-------------|:--------|
|0-4               | SP, LCL, ARG, THIS, THAT
|5-12            | temp
|13-15          | general register
|16-255       | static variable
|256              | stack
|2048           | heap (以下暫時不用管)
|16384         | Screen
|24576         | Keyboard

在 part 1 的最後，我們可以把 assembly 像是 D=A 轉成機械碼 1101...，VM stack machine 程式碼比 assembly 再高階一些，我們可以直接寫stack 操作，例如 push ARG 1，把 Argument 1 推到 stack 的頂端，這樣高階的程式碼讓我們可以更簡單的實作複雜的行為。  

作業是VMTranslator，也就是把剛才那些 push ARG 1 轉成一連串的 D=A, D=M 的assembly，寫作業時發現這份文件非常好用：  
<http://www.dragonwins.com/domains/getteched/csm/CSCI410/references/hack.htm>  

#### 稍微卡的地方：  
pop local 2 這條指令，因為我要先把 local 2 的位址算出來，這樣就需要 D, M, A 三個register 
1. @2
2. D=A
3. @LCL
4. A=M
5. D=A+D

然後要取SP 的位址也需要三個 register
1. @SP
2. A=M
3. D=M

這樣就沒有地方可以存 pop 出來的東西了。  
解法是要用到 13-15 的 general purpose register，算出 local 2 位址之後，先塞進 @R13 裡面，取出stack top 放到D 之後就能直接用 @R13, A=M, M=D 將資料塞進 local 2 裡了。  

對應課程：我其實不確定，編譯器一般不會是編譯成虛擬機 bytecode ，都是直接變成 bitcode；如果說是stack machine 的觀念的話，那就是虛擬機器了。  

## week 2 branching, function call

branch 很單純，一個影片就講完了；大部分的內容都在講 Function Call，這部分最複雜的也就是 Function call 跟 Return 的 calling convention，作業也就實作這兩個功能：  
Function Call 大致的內容如下：LCL (local) 對應一般機器上的 base pointer，SP 則是 stack pointer：  

呼叫函式的部分：  
1. Push argument  
2. 儲存return address, LCL, ARG, THIS, THAT 到 stack 上面  
3. 將 ARG 移動到stack 上存參數的位置  
4. 將 LCL 到stack 頂端  
5. Jump  
6. 寫入Return label   

函式本體的部分：  
1. 執行Push stack，留給 local 變數空間  
2. 函式本體   

Return 部分：  
1. 將 LCL 儲存到 R13 (general purpose register) 中  
2. 將 Return address (LCL - 5) 儲存在 R14 中  
3. 複製 stack 頂端的 return value 到 ARG，要注意沒有參數的話，ARG 指向的位置就是 LCL-5 Return address，所以上面要先把 Return address 備份，不然沒有參數的話會被 return value 蓋掉。  
4. 將 SP 移到 ARG 的位置 (pop stack)  
5. 恢復 LCL, ARG, THIS, THAT  
6. 跳到 R14 的 return address   

如此就完成了函式的呼叫與返回，有一點要注意的事，講義的部分沒有講很清楚：這週的作業有要寫bootstrap 的部分，他只寫要做到

> SP=256  
> Call Sys.init  

其實在Call Sys.init 的部分，也應該要把bootstrap 的 LCL, ARG, THIS, THAT 存到 stack 中，雖然 Sys.init 永遠不會 return，但在實作上還是要求這麼做。  
另外我在寫的過程中，如上所述，函式return 時試著去調換 return value 寫入 ARG 跟取出return address 的部分，結果就把 return address 蓋掉導致 \explosion/ 了，正好驗證那句：「你以為你會寫程式，假的！叫你用assembly 寫一個 Fibonacci 都寫不出來」  

對應課程：這周的對應課程我不甚肯定，calling convention 也許是作業系統，也許是編譯器的 code generation 吧，實際可能分散在下面幾堂課裡：  
計算機結構、作業系統、計算機組織與組合語言、系統程式。  

## week 3 Jack Programming Language

就是介紹 Jack 的設計，syntax, data struct 之類的怎麼設計的，因為Jack 比起什麼C++/Java 簡單非常非常多，說真的只要學過任何一種 programming language 的，這周應該都可以跳過去不用看。  
對應課程：計算機程式。  

## week 4 parser：  

內容介紹 tokenizer 還有 parse 的基本原理，作業是實做 tokenizer 跟 parser，把 jack program parse 成一堆 token 然後寫到 xml 檔中，要產生 token 的xml ，還有parser 處理過，加上結構節點像是 WhileExpression 的 xml。  
tokenizer 我一樣用 python 實作，regular expression 文件裡面有一節就是如何[用 re 的 scanner 來寫一個 tokenizer](https://docs.python.org/3.2/library/re.html#writing-a-tokenizer)，整個 jack language 的規則大概就是這樣，寫起來輕鬆寫意：  

```python
jackkeyword = ['class', 'constructor', 'method', 'function', 'int',
  'boolean', 'char', 'void', 'var', 'static', 'field', 'let', 'do',
  'if', 'else', 'while', 'return', 'true', 'false', 'null', 'this']
tokenSpec = [
  ('comment', r'//[^\n]*|/\*(\*(?!\/)|[^*])*\*/'),
  ('integerConstant', r'\d+'),
  ('symbol', r'[+\-*\/\&\|\<\>\=\~\(\)\{\}\[\]\.\,\;]'),
  ('identifier', r'[A-Za-z_][A-Za-z_0-9]*'),
  ('stringConstant', r'\"([^"]*)\"'),
  ('newline', r'\n'),
  ('space', r'[ \t]+'),
]
```
parser 部分我寫了個class ，對各種狀況寫函式來處理，寫得超級醜，文法檢查和輸出的部分都混在一起了，整個 parser 都是用土砲打造而成，正符合下面這句話：  
「我一直以為我會寫程式…假的！連個 jack compiler 都寫不出來。」  
那個 code 實在是太醜了，決定還是不要公開…，但相較在網路上找到[一些人的實作](https://github.com/kmanzana/nand2tetris/tree/master/projects/10)，連文法檢查都沒有，我是覺得我寫得還是很有誠意啦XD   

對應課程：無疑問的就是編譯器的上半學期  

## week 5 code generation：  

上週實作的編譯器只能輸出 xml ，這周要直接把 jack 轉成 VM code，影片就是一步步教你，當遇到運算符號要怎麼處理，呼叫函式要怎麼處理。它的class 沒有 inheritance 所以…嗯，也不用處理 virtual table 的問題，其實滿簡單的。  
我覺得收獲最大的，是學到怎麼處理物件 method 的call，其實也就是把指向物件的記憶體位址塞進函式的第一個參數，然後在進到 method 的時候先把這個參數塞進 THIS，這樣就能用 THIS[n] 來取用物件的 data member 了。  
這裡也會知道，上面實作時遇到的 THIS, THAT，其實分別對應物件跟陣列，要用物件的 data member 就用 THIS[n] 去取，陣列的內容則用 THAT[n]，這樣只需要把記憶體位址存到 THIS, THAT 裡面，就能取用物件和陣列了。  

下面是一些實作的筆記：  
Jack language 裡面沒有 header/linker 的概念，編譯的時候是以一個 class 為單位在編譯，所以如果裡面出現呼叫其他class 的函式，例如 do obj.foo()，我們只能把它們當成「合法」的程式來產生 code，就算沒有這個 class 或是函式還是可以編譯。  
但沒有最後一步將所有 vm file link成一個檔案，而是模擬器個別 load 所有的 vm 檔，自然不會像 C/C++ 的 linker ，在最後階段回報 `undefined reference to class name/function name` 的錯誤。  

因為parser 已經把整個程式碼變成 AST了，code generate的部分，只需要把對應的函式寫好，大抵就會動了。  
沒實作的地方，我發現與其寫 pass 不如直接 `raise NotImplementedError`，這樣一編譯遇到沒實作的地方，程式就直接 crash 並指出是哪個地方沒有實作。  
而無論是 parser 還是 code generation， `expr->term->factor` 這部分的變化是最多元的，這部分處理完，各個 statement 的部分都可以輕鬆對付。  

然後…它的模擬程式其實有點兩光，如果選用 program flow 模擬的話會非常慢，依它的建議要把它選成 No Animation，可是這個模式無法編輯記憶體的內容；正確步驟是：
1. load 程式
2. 編譯記憶體
3. 選成 No Animation
4. 執行

另外，No animation 下，所有對記憶體的操作，都要按下停止模擬才會反映出來，不知道這點的我一直以為我 code generate 哪裡寫錯了lol。  

這次作業會需要 call 到一些 library 提供的函式，請參考[官方的文件](http://www.nand2tetris.org/projects/09/Jack%20OS%20API.pdf)。  
例如，要產生字串的話，要用 `String.new`, `String.appendChar` 兩個方法，大致如下：  
```python
push constant num_of_character
call String.new 1 # 1 argument
for char in string:
  push constant ord(char)
  call String.appendChar 2 # first is string, second is character
```

最後的 compiler 總共 1000 行左右…覺得實作超糟，都用了python 怎麼還會寫得這麼肥？  

對應課程：編譯器的下半學期  

## week 6 Operating System  

作業系統，或者稱 Library 或是 runtime 應該比較恰當，總之就是 jack 中，會用到一些 Keyboard, Screen, Math 之類的函式，在之前都是用預先編譯好的模組來執行，現在則要自己用 jack 實作這些功能。  
這次的影片也高達 230 分，到最後一個 module 連教授都忍不住大叫：Yeah, the last module~~  

理論上是用 jack 這樣的高階語言來寫，以為有高階語言就沒事了嗎，錯！  
jack 他 X 的有夠難寫，少了一個 do, return 什麼的程式就炸給你看（沒有return 它的函式就會一路執行到下一個函式 lol），因為它沒有 operator precedance 所以該加括號的地方也要加，宣告也無法和賦值寫在一起，我大概照他設計的內容，寫完 Math 跟 Memory 之後才比較抓到該怎麼寫。  
作業寫起來都滿有挑戰性的，像是 Memory.jack 就要用 linked-list 來實作的記憶體管理（用這破破的語言XD）。  

作業不止是在考驗寫 jack ，同時也在驗證上一次寫的 compiler ，測試過程中我找到好幾個 compiler 相關的錯誤，像是函式的參數沒處理好，不該傳入 this 的時候傳入 this，讓我在Output 文字的地方 de 了很久的 bug。  
這種錯真的超級麻煩，你不一定知道是高階語言寫錯還是compiler 錯…，有時要追著模擬器一步步執行，才能知道是哪裡錯了。這次真的是體會到：好的編譯器帶你上天堂，壞的編譯器帶你住套房。  

對應課程：作業系統、系統程式  
有一些些的演算法概念（例如乘法要怎麼實作才會快），但份量極少所以不列上好了。  

## week 7 review
這週只是提點一些 Nand2Tetris 可以加強的部分，像是：  
* 在硬體中實作乘法除法來加速，這樣就不需要 library 的函式支援。  
* 在硬體中實作位元運算（左移右移）  
* 如何自己實作模擬器的 built-in chip  

另外也公佈可能會有的 Nand2Tetris part 3，如何真的在 FPGA 上實作這台電腦  

## 結語：  

大推這門課，課程中 Shimon 講課的速度都滿慢的（我都開 1.3-1.4 倍速在聽課），不會太難聽懂。  
第二部分相較之下實在太難，覺得還是稍微有碰過程式再來學會比較好，第一部分就沒這問題（也許可以說：電機系的不用修第一部分，資工系的不用修第二部分XDD）。  
修完整部 Nand2Tetris ，對數位電路到組成電腦都有一些概念，第二部分更是讓你看透程式到底怎麼編譯、執行，這點可能即使是資工本科生都不一定全盤了解。  
同時，修這門課對我來說也有一點點復健的作用，從簡單的東西入手給自己一點信心：原來，我也是會寫程式，寫得出一些些可以用的東西呢。  

僅引用課程講義最後一節的文字：  
> In CS, God gave us Nand, everything else was done by humans.  
神給了我們反及閘，於是我們打造一台電腦。

另外還有影片中教授引用的這段：  
> We shall not cease from exploration. And the end of all our exploring. Will be to arrive where we started. And know the place for the first time. - T. S. Eliot  
> 我們絕不應停止探索，我們所有探索的終點都會到達我們的起點，並且頭一次了解這個地方 - T·S·艾略特

作為這門課的總結。
