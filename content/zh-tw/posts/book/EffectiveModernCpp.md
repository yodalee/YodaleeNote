---
title: "Effective Modern C++: 42 Specific Ways to Improve Your Use of C++11 and C++14"
date: 2017-04-25
categories:
- BookReview
tags:
- BookReview
- Cpp
series: null
images:
- /images/book/EffectiveModernCpp.jpg
---

|   |   |
|:-|:-|
|書名|Effective Modern C++ 中文版：提昇C++11與C++14技術的42個具體作法|
|原書名|Effective Modern C++: 42 Specific Ways to Improve Your Use of C++11 and C++14|
|作者|Scott Meyers|
|譯者|莊弘祥|
|出版商|歐萊禮|
|出版日|2016-05-04|
|ISBN|9789863478669|
<!--more-->

包括前兩本 effective C++ 跟 more effective C++，其實這已經是作者第三本關於 C++ 的書了，我真的滿好奇作者哪來對 C++ 這樣無比熱情，
因為我已經很久很久沒有寫 C++ 了，有關底層的東西大部分還是用C，雖然有時候遇到沒有STL 支援的資料結構還是會哀一下，
其他程式大多用Python 來寫；寫最多 C++ 的地方大概是 leetcode XD，想練演算法又想貪圖 C++ STL 提供的好處；
大型 C++ 的譔寫經驗好像也沒多少，所以說我到底為什麼要看這本書呢……(思  

扯遠了，先拉回來。  

總而言之，C++ 在 11 跟 14 加入了許多新的語法和功能，這本 Effective Modern C++ 包含42個C++ 的使用項目，分佈在下面7個主題當中：  

* Deducing Types：C++ 的template 是如何推導型別 
* auto：何時該用 auto ，何時又會出錯 
* Moving to Modern C++：C++ 11,14 引入的新的寫法 = deleted, = override, 自動產生的物件方法
* Smart Pointers：推薦使用smart pointer 代替 raw pointer ，以及 smart pointer 背後的實作 
* Rvalue References, Move Semantics, and Perfect Forwarding：C++ 右值的 move, forward 的使用。 
* Lambda Expressions：如何正確使用 C++ lambda 語法 
* The Concurrency API：C++ 提供的 thread 跟 future 要在哪些情況才能正確使用 
* Miscellaneous：其他兩個，介紹 emplace 何時要用 copy-by-value 

我是覺得到了 concurrency API 就已經看不太懂，平常大概也不會用到這樣，不然請大家回想一下你上次用 C++ 寫非同步的程式是什麼時候XD，但前面幾章就還看得滿有感覺的。  

整體來說，C++ 從開始發跡到 C++11, 14，零零總總經歷各種不同的設計，無論是文法上或執行效率的考量，
新增了很多全新的建議寫法或者關鍵字，每個關鍵字的背後可能都是一段故事，就例如存在已久的 
[typename](http://feihu.me/blog/2014/the-origin-and-usage-of-typename)  

書裡每個項目都包含從C++98或 C++11 開始到C++14最新的設計範例，作者還會告訴你為什麼C++11和C++14要這樣設計這些標準，
哪些用法會在造成不預期的結果，或者直接了當的編譯錯誤，我認為，學習 C++ 而不去了解這些故事，等於是錯過一段精彩的設計思辯，非常可惜。  

所以，還是回到那些話：學習C/C++的問題並不是學不會什麼生猛功能，而是要在各種實作的方法中學習：

> 哪些方法是比較<適合>的方法，避免哪些有問題的寫法，比較好的方法和概念是什麼？以及為何如此  

還在感嘆自己不懂C++ 11 跟C++ 14？趕快到書店買本 effective modern C++ 吧  

不過告訴你一個悲慘的事實，今年C++又要推出更新的C++17了，希望今年Scott Meyers 也能再出本新書（More effective modern C++ (誤)）幫大家指點迷津。  

末語只能說：人生很難，可是C++，更難 
