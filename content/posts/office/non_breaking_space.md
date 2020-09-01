---
title: "Word 不分行空白與不分行連字號"
date: 2016-01-28
categories:
- MSoffice
tags:
- word
- non breaking space
series: null
---

今年9月時把之前做的一顆電路整理一下，寫成一篇journal投出去，今天接到學長的回信，結果是Major Revision，一看有不少東西需要改的呀Orz。  
要求修改的內容，有一條是：  

> Through the whole paper the numbers and units should be put into one line for better readability.  
<!--more-->
例如，文中有一些相關的元件單位像是 25 pF，排版時 25 跟 pF 被分到不同行了，這是當時譔寫時沒有注意到的部分；另外負數像 -5 dBm，如果用一般的hyphen 它會被分到不同行去。    

當然這是不可能用手動修正的（要也可以，只是這樣很蠢），這時候我們就需要不分行空白和不分行連字號(non-breaking space, non-breaking hyphen)了，兩者在顯示上和一般的空白和連字號是一樣的，但在排版上word 不會在此字元換行，插入的方法分別是：ctrl + shift + space 跟 ctrl + shift + -    
或者可以在「插入->符號->特殊符號」裡面找到它們。  之後如果遇到不能換行的地方，就插入這兩個符號吧。  

## 參考資料  
<http://savethesemicolon.com/2011/05/16/two_hidden_features_in_microsoft_word>