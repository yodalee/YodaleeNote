---
title: "Modern C"
date: 2016-05-09
categories:
- BookReview
tags:
- BookReview
- c
series: null
---

|   |   |
|:-|:-|
|書名|Modern C|
|作者|Gustedt, Jens|
|出版商|Manning|
|出版日|2019-12-17|
|ISBN|9781617295812|
<!--more-->

本書的全文在網路就[下載得到](https://gforge.inria.fr/frs/download.php/latestfile/5298/ModernC.pdf)，目前也只有英文網路資源，沒有出實體書和翻譯本的樣子：  

從書名和它的序言，作者旨在對 C language 有個基礎的介紹，由於C 的*簡單*，能讓程式設計師快速寫出可以動的程式，例如Hello World，
反倒使人忽略了存在C 背後種種的議題；同時 C經歷多次標準改進，和當年的 K&R C 已經頗有出入，本書從 level 0 - 4，從簡單到複雜再次檢視C 語言中的概念。  

架構其實沒差太多，從控制結構、資料型別、array, struct, enum 等等，書中不時列出一些 **Rule**做為重點提示，像是建議、警告，
和一般C 語言的書比較不同是，它會去討論一些背後的概念，例如unsigned int 的值是如何得來；
comma operator 回傳最後一個expr 的定義不小心會讓你debug 超久；各種資料型別極限值與轉換時數字的變換…  

雖然個人寫C 也有一段時間，不過重新細看書內的介紹，還是會發現一些之前沒想過的陷阱，有些章節例如第九章是 C Coding Style，
可能會引發宗教戰爭(X，覺得已經純熟的章節可以看過去就好。  

最後的 Level 4: Ambition 可能是我目前看過C language 相關最有野心的一章，大多數 C lang 的書只專注在「把C 講好」這件事，
Ambition 這章跟現行的C 語言無關，而是提出作者的見解：如何修改標準「讓C 更好」。  
如果只是想更親近C 語言的人，可以明正言順的略過這章，畢竟這章節需要對C 標準、編譯-器實作與程式最佳化有更多認識後，
才能理解箇中大意與作者意圖，不然只是看著書中列出一段C standard，說應該改成怎樣怎樣，應該不用五分鐘就可以安然入眠了，個人最後也是看得一頭霧水QAQ  

要我說對這本書的整體心得，該說隨著C/C++ 標準進化的同時，更適合的寫法也推陳出新，絕對避免的寫法也所在多有，
但很無奈的為了相容之前的標準，過去的用法會一直留在那裡，等待天真不知情的新手程式設計師去踩雷然後`~~~~~~~~EXPLOSION~~~~~~~~`  

學習C/C++的問題並不是學不會什麼生猛功能，而是要在各種實作的方法中學習：

> 怎麼用比較<適合>的方法來實作，避免哪些有問題的寫法，比較好的方法和概念是什麼？為何如此  

像是避免用scanf 造成overflow 的bug，這需要程式設計師去學習正確的寫法；之前所寫的option type，強者我同學的註解：
「C++ boost 已經收入option，之後很可能也會收入標準」  
但null pointer 在C++中仍然允許，寫出Girl *gf = nullptr 讓 nullptr 把程式炸了無疑是合法的，
畢竟C/C++ 都假定程式設計師是聰明人，會對自己寫的code 負責。    

這本書前半部未必適合新手程式設計師，比較適合已經有些了解的人，再次檢視自己所學的內容；
後半部則適合對C, OS, compiler 都有詳加研究的，栽進去與作者一同讓這款有44 年歷史的語言更加完善。 