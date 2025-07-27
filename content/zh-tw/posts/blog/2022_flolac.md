---
title: "第一次參加 FLOLAC 就上手"
date: 2022-08-13
categories:
- LifeRecord
tags:
- haskell
- flolac
series: null
images:
- /images/blog/flolac2022.jpg
---

故事是這樣子的，雖然已經是社會人士但還是要定時學一點東西，COSCUP 一結束，
緊鑼密鼓就接著兩個星期的邏輯、語言與計算暑期研習營 FLOLAC 2022，一個~~FP 宗教人士們的神祕聚會~~關於邏輯以及函數式語言的暑假短期課程。

小弟之前研究所認識的大大現在在當助教，也有上過課的教授是本次課程的教授之一，就決定在工作之餘參加一下。
<!--more-->

# Functional Programming 與我

為什麼要報名這堂課呢？其實說起來有點話長

個人對於 Functional Programming （下稱 FP）一直有種距離感，第一次見識到 FP 應該是在研究所修 compiler 的時候，
小弟還在苦苦學習怎麼寫 C 跟 lex/yacc，隔壁的大大直接用 Haskell 的 Happy Parser 弄出一套 C compiler，覺得實在是太神啦。  
之後就在 coursera 上面聽了 [Functional Programming Principles in Scala](https://www.coursera.org/learn/scala-functional-programming) ，
記得學到咖哩左右就放棄了，算是一次印象不太良好的初體驗。

第二次接觸就沒那麼明確，大概列一下有：
1. 當兵的時候因為 jserv 大大的推薦看了 [Understanding Computation](https://computationbook.com/)，
從六、七章出現了一些跟 FP 有關的概念，如 church encoding、lambda calculus、其他 calculus 等等

2. 在某年的時候在 cousera 上了的 Programming Language 
[Part A](https://zh-tw.coursera.org/learn/programming-languages), 
[Part B](https://zh-tw.coursera.org/learn/programming-languages-part-b), 
[Part C](https://zh-tw.coursera.org/learn/programming-languages-part-c)，有兩節用的是 FP 的 SML 跟 Racket

3. 在 2015 年接觸了 Rust，雖然在剛接觸的時候並不知道它跟 FP 的淵源，我想多少因為這樣而在 Rust programming 上吃很大的虧，
花了一年多的時間透過實作 Understanding Computation 把 Rust 能力建立起來。
4. 在 2018 年修了一門資管系的程式語言正式學到 Haskell，摸著摸著突然發現 Rust 根本從 Haskell ~~抄襲~~借鑑了一堆東西，

後來呢？  
疫情前還偶爾會參加一下 Functional Thursday，疫情後好像就沒有什麼跟 FP 有關的東西；
頂多是在 Hardware 議程軌上，認識了 SpinalHDL 這種 FP HDL，聽說每個寫硬體的人都敬謝不敏的東西；
真要說的話，最接近 FP 的東西反而可能是 Rust 這種血統不純正的傢伙XDD。

總歸來說就是若即若離，知道這個東西不過也不算多知道，例如你突然叫我用 Haskell 寫個什麼程式，有八成機會我是無法有效率地寫出來的。  
也許是機運吧？
剛好在報名期間注意到 FLOLAC，想想假留了這麼多，今年可能是因為武肺而不能出國的最後一年，之後的假不能這樣豪邁的浪費掉，就跟公司請假報名下去了。

# 報名

在報名的時候會一些要求：
1. 看書：[learn you a haskell for great good](http://learnyouahaskell.com/)，要求要看 1-6 章跟第八章；
這本之前有用通勤時間看過一次，這次就沒有重看了。
2. 寫作業，證明你確實看得懂 Haskell 的語法，我寫的 code [丟在 Github 上](https://github.com/yodalee/FLOLAC22)，
~~給大家白天讀書晚上工作假日批判~~。

# 上課


從 8/1 開始上課，課程分上下午，上午 09:10-12:10 三節課一單元，下午 13:10-16:10 三節課一單元，總共上滿 16 堂課。  
上班這麼久之後，突然回歸學校，天天早上 09:00 到台灣大學的新生大樓上課，下課之後去活大~~吃到飽~~吃 40 元素食（這家完全沒漲價也是很厲害）下午再上三堂課，實有太青春了一點。

第一天到的時候覺得這感覺太懷念了，好像以前在上微積分的感覺，還拍了一張照片：
![0900 school](/images/blog/flolac2022.jpg)

看看[官方網站下面的課表](https://flolac.iis.sinica.edu.tw/zh/2022/index.html)的話，主體可以分為四個部分：

1. 函數程式設計
2. 邏輯
3. λ-calculus
4. Monad 與副作用
5. 使用 agda

為什麼會有五個呢，我們下面會說明~~因為四大天王有五個是常識~~：

## 函數程式設計
介紹 Haskell 程式的證明，例如怎麼用 haskell 的
```haskell
length [] = 0
length (x:xs) = 1 + length xs

[] ++ ys = ys
(x:xs) ++ ys = x : xs ++ ys
```
證明
```haskell
length (xs ++ ys) = length xs + length ys。
```

不過這部分跟我在 2018 年程式語言的內容是重複的，很輕鬆寫意就過去了。

我覺得有點鳥的就是，繼承這位教授的一貫風格進度都會 delay，
理論上大家寫過作業對 Haskell 語法應該是要夠熟的，有些內容應該不用重講，
不過算是小問題，~~畢竟工作的 project 也會 delay 上課 delay 算什麼~~。

## 邏輯

介紹基本的邏輯推理，怎麼用一套符號系統來證明我們需要的命題，例如從 A, (A->B) => B
這個因為我也是在 2018 年左右修過 coursera stanford 的 [introduction to logic](https://www.coursera.org/learn/logic-introduction)
（對我 2018 年那段時間超認真下班就修課……），所以也算了解那個內容。

用的符號有點不太一樣就是，introduction to logic 用的是 fitch system ，但背後思路都差不多；
另外 coursera 專注在邏輯上面，這裡是一路推到 lambda 那邊去了。

## λ calculus

這部分看的是 lambda calculus 的基本理論，如果要我說的話，講的內容跟 understanding compuation 第六章 Programming with Nothing 的部分是一樣的。
Programming with Nothing 裡面的兩節就是
1. church encoding 實作 fizzbuzz
2. 實作 lambda calculus 及其 reduce

我是覺得可以的話，能把 understanding computation 的第六章當個課前讀物，也許大家會更有概念一些，不過這本書要付費就是了。

## Monad 與副作用

以實用度來排名的話，個人覺得這章應該是最高的，說得誇張一點，學過 Monad 才有能力用 Haskell 寫一些有用的程式~~例如發射飛彈~~。  
畢竟整個 Haskell 程式就是包裏在一個巨大的 IO Monad 下面，如果不會 Monad 可能連 main 都不知道為什麼要這樣寫，
頂多玩玩 pure function；但 pure function 就沒有實用價值。

這段就是對 Haskell 理解能力有些要求，但我個人覺得還行，整個教材用了從簡單到複雜的填空程式，
不斷做重複但有點小變化的東西，讓你抓到 Monad 設計的目的是為了取代（虛擬化）什麼。

另外在這段學到的程式設計流程也滿值得記下來的：

> 型別->用途->範例->策略->定義->測試

最近個人有偏好強型別的傾向，型別定好再由工具幫你檢查真的寫起來舒服很多，不會犯一些奇奇怪怪的低級錯誤。

## agda

多加進來的這章有三堂課，分別對應<函數程式設計>、<邏輯>、<λ calculus>。  
課堂上會用 agda 這套……我也說不出來這算什麼鬼，雖然是程式語言但用起來實在不太像，我覺得比較像 meta-language……的東西，
去證明我們之前推過的式子都是正確的。  
這段真的難度頗高的，很像修邏輯時用的那個 javascript 破系統，你下對的指令它就幫你做對的事，下錯了它就雙手一攤。  
agda 雖然功能強大，但你也要懂它的脾氣才行，不然它就會一直跟你說 cannot refine 然後什麼事都做不成。

# 總結

我個人來說的話，這堂課有大半是複習，有滿多東西都是以前知道，就是再聽一次加強記憶跟理解。  
如果從實用程度來看，Monad 應該是最實用的吧，haskell programming 可能次之，邏輯跟 λ calculus 就……比較理論一點，
以一位工作人的角度來看，理論派上用場的機會微乎其微，但知道還是滿有趣的。

成果來看我自評大概是：
* 50% 的感覺是學習概念，對我的 coding 也許有幫助，邏輯、lambda 、haskell、monad
* 40% 是這個東西知道的話也許有一天會派上用場，是哪一天不知道，比如說 agda
* 10% 是眼下看來可以立即上場的東西

至於我推薦嗎？如果是大學或研究所，我應該會大力推薦修一下；如果對 FP 有極度熱忱的話也滿推薦的，
像我現在對 Haskell Monad 概念熟了很多，比較有自信能看得懂 Haskell 含 Monad 的程式了。  

如果已經在工作，而且工作、生活上的經驗跟 FP 沒什麼關係的話，就沒什麼修課的必要，畢竟 9 天的休假請下去也是滿痛的。

另外每年的課表似乎會是不一樣的，例如今年有 Monad 但兩年後可能就沒有了，所以其實也可以報名，
然後看看課表，選有興趣的內容去聽就好了 ;)
