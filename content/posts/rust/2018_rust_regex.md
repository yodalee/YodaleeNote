---
title: "寫了一個不知道幹什麼用的 regex library 跟 parser"
date: 2018-08-17
categories:
- rust
tags:
- rust
- regex
series: null
---

故事是這樣子的，之前寫 understanding computation 的時候，發現 regular expression 的實作，只有最基本的五種：
* empty 匹配空字串
* literal 匹配文字
* repeat * 匹配零個或多個 regex
* concatenate 匹配連續的 regex
* choose 匹配嘗試數個 regex  

大約幾天前想到也許可以把這個 project 拓展一些，讓它威力更強力一點點，順便當個練習。  
<!--more-->

預計要加入的東西有：  

* 支援 +, ? 兩種擴展的重複方式。
* 支援 “.” 匹配 any character。
* 支援 "[]", "[^]" 匹配在/不在集合中的字元。

+跟? 是最簡單的，它們和狀態機的設計無關，只要修改產生狀態機的方式即可；
"*" 的時候是引入一個 start\_state，將 start\_state 和原本狀態機的 accept\_state 加入新的 accept\_state，並用 free\_move 將 accept\_state 跟原本狀態機的 start\_state 連起來。  

* \+ 的話是新的 start\_state 不會是 accept\_state 的一員。  
* ? 的話是原本狀態機的 accept\_state 不會用 free\_move 和 start\_state 連線。  

any 相對也很好做，本來我們的 farule 是一個 struct ，現在變成一個帶 enum type 的 struct，該有的都有：
一個 state 到另一個 state；取決於 enum type ，會使用不同的 match 規則來決定適不適用規則。  
像是 Any 就是全部都適用，literal char 的話會是比較一下字元是否相同。  

[] 的實作…我發現到之前的實作，不太容易實作出 [^] 的規則。  
[] 相對容易，簡單看來它就只是把裡面所有的字元變成 choose rule，例如 `[a-z] -> a|b|c..|z`，但 [^] 就不同了，
因為在 NFA 裡面，一個輸入的字元會跟所有可以嘗試的 rule 去匹配，但我們不可能把 [^] 之外所有的字元都接一個 choose 去 accept state （好吧理論上可以），
如果在 `[^a-z]` 把 a-z 接去一個 dummy state， 用一個 any rule 接去 accept state，表示任何輸入的字元在嘗試 any rule 的時候都會通過它漏到 accept state 去。  
最後還是在一條 rule set 裡面，保留所有可匹配字元的方式解決 QQ，這樣一來 match 一個字元的 rule 就變成這個 rule 的子集
（不過為了方便還是保留這個 rule），接著 regex 的 [][^] 就只是直接轉譯成 Rule set 就行了。  

剩下的應該就只有改一下 PEG parser，這部分比較沒什麼，其實寫這個 project 沒什麼突破性的部分，大部分都是做苦工，好像沒什麼好值得說嘴的。  
而且這樣改還有一個後遺症，就是匹配變得只能在 NFA 下進行，不能轉成 DFA 來做了，因為如 rule any, rule set 都會讓我們無法走訪目前所有可能的匹配結果，
目前我看到市面上(?) 的 regular expression 實作，也都不是用這種 NFA 的方式在實作的，所以說我寫這個 project 到底是為了什麼……。  

寫文章附上[原始碼](https://github.com/yodalee/nfa_regex)是常識我知道我知道  

當然還是有一些好玩的東西，例如[測試](https://github.com/yodalee/nfa_regex/blob/master/src/regular_expressions/mod.rs#L132)可以任我寫  