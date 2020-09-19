---
title: "Cryptography 1"
date: 2015-11-02
categories:
- coursera
- cryptography
tags:
- coursera
- cryptography
series: null
---

在陰間為了殺時間，總要找點書來看，因為自知不能看一些會變的東西，例如程式 Rust；這種東西等我返陽搞不好都翻了兩翻，現在我主力放在兩個方向，一是修coursera 的cryptography 課程，二是閱讀Logan 大大推薦的 Enginnering a compiler，前一個 cryptography 1 課程剛結束，這裡記錄一下心得。  

下面是基本資訊：  

|   |   |
|:-|:-|
|課程名稱 | Cryptography I  |
|開課學校 | Stanford University   |
|授課教授 | Dan Boneh
|開課時間 | 6 周   |
|教學方式 | 影片授課   |
|通過方式 | 每週完成指定的作業並完成線上測驗。   |
<!--more-->
這門課不算太難，帶過密碼學上幾個重要的概念：Stream cipher, Block cipher, Asymmetirc cipher，人人都怕的數學只在非對稱式加密前帶過一些。  
上課的內容還有授課方向，跟這本 [understanding cryptography](https://link.springer.com/book/10.1007/978-3-642-04101-3) 非常相似，打書名就能找到這本書的全文電子檔；兩者搭配來看，可以補線上課程內容的不足。  

程式作業有6題，只有一個是要求用現有的 AES lib 來實作 CBC 跟CTR 加密，另外五個都是利用已知的漏洞去破解某些密文，就跟教授上課不斷提醒的："Don’t invent your own ciphers or modes"。  
作業藉實際攻擊讓大家了解，即使數學理論上安全的加密，在不正確的實作下，仍會導致安全性流失，寫程式會需要一些底子，不過只要會python 或C++應該不算太難。  
從程式作業，真的可以體會密碼的設計是一門高深的學問，倒也不是說不要去實作和修改，否則一些知名的 lib 像 openSSL 是誰在維護？而是要先學好基本概念，了解可能的弱點與攻擊方式，多和大家討論分享實作方式，有討論才有進步。  

俗話說得好：「三個臭皮匠勝過一個諸葛亮」，密碼學因為攻擊方式千變萬化，絕非一位天才能掌握全部面向，許多科技領域也是如此。  
在這個年代作為一個工程師，我認為最有效的學習是先學會基本概念，用一些簡單的例子實作驗證這些概念，再去找其他一流的project參與。  
之所以不要一口氣去跳進一流的project，是因為那裡一定藏了一堆實作細節，會遮掩掉基本概念；千萬不要閉門造車，分享你的想法，才有更大的進步空間。