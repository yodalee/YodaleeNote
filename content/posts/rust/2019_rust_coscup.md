---
title: "從 Coscup 小談 Rust"
date: 2019-11-04
categories:
- rust
tags:
- rust
- coscup
series: null
---

這篇其實有點拖稿，畢竟 COSCUP 都是幾個月前的事了；這次在 COSCUP 投稿了 Rust 議程軌，覺得可以來說說對 Rust 的一點感想。  
Rust 從問世、正式發佈到現在也差不多要 7 年，感覺近年來有愈來愈紅的趨勢，一種社群上面看一看發現大家都用過 Rust 的感覺。  
<!--more-->

今年的 COSCUP 專門開了一個 Rust 議程軌，而且感覺議程的內容正在提升，不再是一堆語言介紹，
有更多的是在介紹用 Rust 實作的資料庫、web assembly 、類神經網路的應用，可以預見 Rust 正在走出推廣階段，前往實際應用的領域。  

不過我們還是要回來問，Rust 在哪裡會有<十倍生產力>？也就是在哪裡可以把東西做得比其他語言十倍好，像是要推人工智慧大家就會推 Python；
要寫高效能的網路可能會用 golang，有哪個領域是非用 Rust 不可的嗎？  
現在有些風聲是區塊鏈的合約和交易語言，但我對這塊應用的大小有點存疑。  

Rust 天生尷尬在它的定位上，它的目標是一個安全高效的系統程式語言，它也的確有潛力做到這點，
但整體看來 Rust 可能是幾大系統程式語言裡數一數二複雜的，可能只輸給 C++，配上最新加上去的 Async 可能差不多就比肩了(欸。  

確實 Rust 從源頭來看，受到大量函數式語言和語法的啟發，語法上看得出核心來自一個優異的語言團隊並吸收了各類語言的優點；
編譯時進行的所有權確認和以 mod 為編譯單位，雖然讓 Rust 編譯慢得像烏龜，卻也大量消除程式在執行時出錯的機會，或者因為設計師**忘記**而導致的問題。  
Rust 不可能是一款早期的語言，它浪費太多運算資源在編譯檢查，在 C 語言發跡的年代不會浪費資源去做那些檢查，
換來的就是 Rust 編譯器數一數二的 GY 程度，這個不行那個也不行，搞得寫 code 的人跟編譯器都很累……。  

我認為 Rust 要走的會是一條很艱難的道路，Rust 內建的複雜性天生就拒絕了一些簡單的應用，用 Rust 寫起來太過繁瑣了，
動態語言能搞定的網路服務開發速度是第一，程式設計師上手的速度還有開發的速度來看，沒理由不用動態語言；
而一些偏底層的應用，特別是對從 C/C++ 來的人來說，Rust 根本就不可理喻，明明我用 C 系列一下就可以搞定的，誰跟你在那邊 4 種 String 還有一堆 Option 要處理？  
一眼看穿的程式實在用不上 Rust，有人覺得 Rust 可以在嵌入式系統上挑戰 C，我看再過 100 年都不太可能。  
Rust 的優勢，要來到所謂的大型系統程式才會出現，透過編譯器的強制，把一些難以檢測到的記憶體問題給挑出來，
當然用 C++20 的一些特性可以做到一樣的效果，但沒有編譯的強制只靠設計師所受的教育，在大型系統下畢竟不是一個妥當的做法，
畢竟設計師也是人，不可能不犯錯，或者偷懶或者忘記，一不小心就引入 C++ 的舊語法 -- 那些為了向後相容絕對不會移除的部分。  

但問題就在於：大型系統幾不太可能整個重寫，更別提底層所依賴的都是經過千錘百鍊的 C/C++ 函式庫，
像 Mozilla 那樣決定把瀏覽器核心整個抽換掉真的是~~神經~~勇敢，市面上的大公司哪幾家做過一樣的事？  
可以預期 Rust 幾年之內，都會是用滲透的方式慢慢進到各大公司的系統當中，也許是一個新實作的子系統或是重寫某些小部分，
用 FFI binding 的方式和既有的系統銜接，但要成為主流我看還要努力一段時間才行。  

其實我是覺得語言比語言氣死人，不過 Rust 對 go 一直是一個大家很有興趣的話題（雖然說兩個根本是完全不同的東西），
我個人滿推薦 LoWeiHang 翻譯的[這篇文章](https://gist.github.com/weihanglo/3dc1af4b0c15cb9ec600f28a7b06ad2f)。