---
title: "從 blogger 轉換到靜態網頁生成"
date: 2020-08-20
categories:
- LifeRecord
tags:
- blog
series: null
---

看到這個標題大概就知道發生什麼事了……。  
是的，經過十年 blogger 寫作，我終於決定要搬家了。  
<!--more-->

故事是這樣子的，自從 2011 年起我就持續的有在寫 blog，那時候選的是 google 的 blogger 服務，剛看一下到目前為止總計 246 篇文章，
算上這篇搬家文的話是 247（剛好是 13 * 19 ，可以當作 RSA 公鑰），大部分都是技術相關，也有部分是生活雜記跟書評等等。  

總括來講 blogger 並不是不好用，相反的 blogger 提供可以用瀏覽器編輯內容、圖片上傳後自動歸檔到近乎無限的 google 雲端
（這另一方面也是一個問題，刪除誤上傳的照片很麻煩）、google 在背後保證了網站的可及性和穩定度、手機與電腦都支援的瀏覽介面，
如果你對網誌內容沒有什麼太嚴謹的要求，只是想要記錄一下生活貼貼遊記照片，blogger 已經大概有 80 分吧。  
特別是不要以今非古，以那個年代的網路環境，找免費空間架站還不是那麼容易的事，託管在 google/blogger 顯然是簡單很多的解法。  

blogger 的缺點，最後逼得個人跳槽的最大原因，我認為是：程式碼與凌亂的文章格式。  
畢竟個人的 blog 從開始的定位就不是簡單記錄生活就算了，我非程式相關的文章大概 30 篇左右，程式相關內容佔了 80 % 以上，而程式碼是 blogger 最弱的一環，目前我寫作 blogger 的工作流程通常是這樣子：  

1. 在 google doc 上面完成，我一個文件叫 write anything ，想寫什麼就全部往裡面倒。
2. 整理成文章，把文章內容複製到 vim。
3. 透過之前寫好的 [blogger.vim]({{< relref "vim_blogger.md" >}}) 將文章內容要劃重點、程式碼的部分加上 tag。
4. 用 blogger html 編輯器，直接將全篇文章貼入。
5. 在 blogger 一般編輯器，幫文章加上連結、圖片等。
6. 來回檢視預覽和編輯器，修正所有顯示不如預期的地方。

是的，我的文章從來不用 blogger 的編輯器，都是全部生好 html 再整個貼進去，程式碼的部分利用 
[pretty-print 套件](https://github.com/googlearchive/code-prettify)（剛剛看到它 archive 了…）為 `<pre>` 上色，
或是 pretty-print 失效時加上 `<div>` 標籤加框，幾乎每次編輯 blog 都一定要去改動 html，搞得寫程式相關文章變得很痛苦。  

第二點也是我為何都用 html 編輯器的原因，透過 blogger 編輯器產生的內容格式非常不穩且難以維護，生出來的 html 簡直嘔吐物，
很難再去手動修改 html ，但如上所述在寫文的時候去改動 html 幾乎是必要的，只能用編輯器的功能把所有格式都清除掉，那還不如一開始就寫 html 就好。  

特別是這幾年開始寫 rust 相關文章之後，上述問題整個變本加厲，因為 rust 特有的生命周期語法，會讓 pretty-print 的上色功能大噴射
（它會以為 lifetime 'a 是字串開頭，其實根本不是…），每寫一篇 rust 的文章想跳槽的意念就深一層，
最近的 [amethyst 系列]({{< relref "posts/amethyst/introduction.md">}})真的是壓垮 yodalee 的最後一根稻草，
系列文完成前就決定跳槽，想要看完 amethyst 系列文的朋友只好說聲對不起了。  

這次跳槽的目標是轉換為 static site generator，其實這幾年來陸續都有朋友推薦這種寫作方式，但礙於懶得搬移舊文章一直沒有動手，
推薦的工具也從早年的 [Ruby/Jekyll](https://jekyllrb.com/) 到最近改推 [Go/Hugo](https://gohugo.io/) 了；
本來我是想說身為 rust 使用者，應該選擇 [Rust/Zola](https://www.getzola.org/)（hail hydra…欸），
只是後來發現 zola 的 theme 實在太少了，還是先用 hugo 撐撐場面。  

廢話不多說，讓我們來開始著手搬家吧。