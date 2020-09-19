---
title: "用 PEG 寫一個 C parser"
date: 2018-08-25
categories:
- rust
tags:
- rust
- c
- parsing expression grammar
series: null
---

故事是這樣子的，之前我們寫了一個自創的程式語言 [Simple Language]({{< relref "2018_rust_simple.md">}}) ，
還用了 Rust 的 [pest](https://github.com/pest-parser/pest) 幫他寫了一個 [PEG parser]({{< relref "2018_rust_pest_PEG">}})，
雖然說它沒有支援新加入的函式等等，本來想說如果年底的 MOPCON 投稿上的話就把它實做完，結果沒上，看來是天意要我不要完成它（欸  

總而言之，受到傳說中的 jserv 大神的感召，就想說來寫一個複雜一點的，寫個 C language 的 PEG parser 如何？
然後我就跳坑了，跳了才發現此坑深不見底，現在應該才掉到六分之一深界一層吧 QQQQ。  
<!--more-->

目前的成果是可以剖析 expression 並依照正確運算子順序處理，還有部分的 statement 也能正常剖析，
因為通常能處理 expression 跟 statement 剖析裡麻煩的工作就完成 50 %，決定寫小文介紹一下，
啊不過我還沒處理 expression 出現轉型的時候該怎麼辦，array reference 出現要怎麼辦，所以這部分可能還會改。  
本來專案想取名叫 rcc 或 rucc，但這樣的專案名稱早就被其他人的 rust c compiler 用掉了，
因為寫 Rust 的人好像都很喜歡用元素來當專案名稱，這個專案的名字就叫 Carbon 了XD。  

其實寫這個跟寫 simple parser 沒什麼差，只是語法更加複雜，複雜之後就容易寫得沒有結構化；
PEG 有個好處是在處理基礎的結構的時候，比起用 regular expression 各種複雜組合還要簡潔，像是 floating point 的時候，
這是 C floating point 的語法，雖然這還不含 floating point 的 hex 表達式，但不負責任的臆測，要加上 hex 的支援只要多個 (decimal | hex) 的選擇就好了：  
```txt
sign = { "+" | "-" }  
fractional = { digit* ~ "." ~ digit+ | digit+ ~ "." }  
exponent = { ("e" | "E") ~ sign? ~ digit+ }  
floating\_sfx = { "f" | "F" | "l" | "L" }  
floating = @{ fractional ~ exponent? ~ floating\_sfx? }   
```
不過脫離基本結構，開始往上層架構走的時候麻煩就來了。  

我的感想是，在大規模的語言剖析上 PEG 其實不是一個很好用的剖析方式，寫起來太隨興，沒有一套科學分析的方法告訴你怎麼樣寫比較好，甚至怎麼寫是對的，
就連 C standard 的寫法都是用 CFG 可以處理的格式寫的，PEG 畢竟比較年輕才沒人鳥它；
在傳統 CFG，List 就是用 List -> List x 那套來表達，在 PEG 裡卻可以直接把剖析的文法用 +, * 重複，層數相較 CFG 可以有效扁平化，
相對應的壞處是很容易寫到壞掉，目前為止花了很大的心力在調整語法各部分的結構，非常耗費時間。  

例如在剖析函式的內容，C 語法大概是這樣定義的：  
```txt
compound_statement -> block_list
block_list -> block_list block
block -> declaration_list | statement_list
declaration_list -> declaration_list declaration
statement_list -> statement_list statement
```

上面這段大致體現了 declaration 跟 statement 交錯的寫法，一開始寫的時候，直譯就翻成  
```txt
compound_statement -> block*
block -> declaration* ~ statement*
```
很直覺對吧？但上述的語法會直接進到無窮迴圈，上下層兩個連續的 * 或 + 是 PEG 語法的大忌，
當上層跳入 * 無窮嘗試的時候，下層就算沒東西 match 了，照樣可以用 * 的空集合打發掉；
同理上層是 + 下層是 * 也不行，理由相同；真正的寫法是上層用 * ，下層用 + ，在沒東西的時候由下層回傳無法匹配讓上層處理。  

這個例子最後的寫法其實是這樣：  
```txt
compound\_statement -> block*  
block -> (declaration | statement)+   
```

或者是這樣，反正轉成 AST 之後也沒人在意 block 到底是只有 declaration 、只有 statement 還是兩個都有，乾脆把所有 declaration 跟 statement 都攪進一個 block 裡：  
```txt
compound\_statement -> block  
block -> (declaration | statement)*   
```

這個例子很明顯的體現出 PEG 文法的問題，透過文法加上 `?+*`，我們可以很有效的把本來的 list 打平到一層語法，但連接數層的 `+*` 就需要花費時間調解層與層之間的融合，是一件複雜度有點高的事情。  
很早之前在看參考資料的時候有看到這句，現在蠻有很深的體會：

> 我覺得用 PEG 類工具可以很快的擼出一個語法，是日常工作中的靠譜小助手，但要實現一個編程語言什麼的話，還得上傳統的那一套。

（註：原文為簡體中文此處直翻正體中文）  

像是我的 simple parser 跟 regex parser，用 PEG 寫起來就很簡明，一到 C 這種複雜語言就頭大了；
CFG 那邊的人大概會指著 PEG 的人說，你們 PEG 的人就是太自由了，哪像我們當年（誒  

剖析寫完再來還要把文法轉譯成 AST。  
在實作上大量參考強者我學長 suhorng 大大的 [haskell C compiler 實作](https://github.com/shhyou/compiler13hw)，
想當初跟學長一起修 compiler，那時候我還很廢（其實現在也還是很廢），光是寫 C lex/yacc 能把作業寫出來不要 crash 就謝天謝地了，
然後學長上課的時候 haskell 敲一敲筆電就把作業寫完了 QQQQ。  

用 rust 的 pest PEG 套件寫轉換的程式，大部分都是 match rule ，看是哪種 Rule 之後去呼叫對應的函式來處理。  
在expression 的部分可以直接使用 pest 提供的 precedence climbing 功能，無論是文法或建 AST 都很簡單，文法甚至可以收到一行，因為 expression 都是一樣的格式：  
```txt
expression -> unary_expr (binary_op unary_expr)* 
```
再到 precedence climbing 為所有 op 分出順序，就像 climb.rs 裡面那壯觀的 C operator 優先次序：   
```rust
fn build_precedence_climber() -> PrecClimber<Rule> {
  PrecClimber::new(vec![
    Operator::new(Rule::op_comma,    Assoc::Left),
    Operator::new(Rule::op_assign_add,   Assoc::Right) |
    Operator::new(Rule::op_assign_sub,   Assoc::Right) |
    Operator::new(Rule::op_assign_mul,   Assoc::Right) |
    Operator::new(Rule::op_assign_div,    Assoc::Right) |
    Operator::new(Rule::op_assign_mod,  Assoc::Right) |
    Operator::new(Rule::op_assign_lsh,    Assoc::Right) |
    Operator::new(Rule::op_assign_rsh,    Assoc::Right) |
    Operator::new(Rule::op_assign_band, Assoc::Right) |
    Operator::new(Rule::op_assign_bor,    Assoc::Right) |
    Operator::new(Rule::op_assign_bxor,  Assoc::Right) |
    Operator::new(Rule::op_assign_eq,     Assoc::Right),
    Operator::new(Rule::op_qmark,    Assoc::Right) |
    Operator::new(Rule::op_colon,    Assoc::Right),
    Operator::new(Rule::op_or,       Assoc::Left),
    Operator::new(Rule::op_and,      Assoc::Left),
    Operator::new(Rule::op_bor,      Assoc::Left),
    Operator::new(Rule::op_bxor,     Assoc::Left),
    Operator::new(Rule::op_band,     Assoc::Left),
    Operator::new(Rule::op_eq,       Assoc::Left) |
    Operator::new(Rule::op_ne,       Assoc::Left),
    Operator::new(Rule::op_gt,       Assoc::Left) |
    Operator::new(Rule::op_lt,       Assoc::Left) |
    Operator::new(Rule::op_ge,       Assoc::Left) |
    Operator::new(Rule::op_le,       Assoc::Left),
    Operator::new(Rule::op_lsh,      Assoc::Left) |
    Operator::new(Rule::op_rsh,      Assoc::Left),
    Operator::new(Rule::op_add,      Assoc::Left) |
    Operator::new(Rule::op_sub,      Assoc::Left),
    Operator::new(Rule::op_mul,      Assoc::Left) |
    Operator::new(Rule::op_div,      Assoc::Left) |
    Operator::new(Rule::op_mod,      Assoc::Left),
  ])
}
```

match 之後一定有些規則是無法處理的，例如 match statement 的時候就不用管 op\_binary 的 rule，這裡我寫了一個函式來承接這個規則，
Rust 函式的 ! 型別相當於 C 的 noreturn，已經確定這個還是不會回傳值了，印出錯誤訊息後就讓程式崩潰；這個函式就能在任何 match 的分枝上呼叫。   
```rust
fn parse_fail(pair: Pair<Rule>) -> ! {
  let rule = pair.as_rule();
  let s = pair.into_span().as_str();
  unreachable!("unexpected rule {:?} with content {}", rule, s)
}
```
這樣這個函式就能出現在任何地方，例如 match 當中，每一條分支都應該要得到同樣的型別，不過這個函數可以是例外，畢竟它確定不會再回來了：  
```rust
match (rule) {
  Rule::op_incr => Box::new(CastStmt::StmtPostfix(CastUnaryOperator::INCR, primary)),
  Rule::op_decr => Box::new(CastStmt::StmtPostfix(CastUnaryOperator::DECR, primary)),
  _ => parse_fail(pair),
}
```

我自己是覺得，把 PEG 文法剖析出來的結果轉換到 AST 上面，麻煩程度差不多就跟寫一個 recursive descent parser 差不多，
而且用了 PEG 套件很難在使用者給了不正確程式時，給出有意義的錯誤訊息，我用的 pest 最多只能指著某個 token 大叫不預期這個 token ，預期要是哪些哪些。  
到頭來要給出好一點的錯誤訊息跟發生錯誤的回歸能力，也許還真的只能像 gcc, llvm 一樣，直接幹一個 recursive descent parser。  

不過以下是我不負責任的想法，我我暗暗覺得 PEG 的語法和 recursive descent parser 之間應該有某種對應的關係，
也就是說，如果設計好 PEG ，應該能給出一個不錯的 recursive descent parser 的骨架，
搭配使用者設計好在哪些文法遇到哪些錯誤該如何處理函式群，生出一個 recursive descent parser 來；不過以上只是不負責任的臆測，請各位看倌不要太當真。   

這個[專案](https://github.com/yodalee/carbon)其實還在草創階段，還有超多東西沒有支援（其實連個像樣的功能都沒有吧...），各位看倌大大手下留情QQQQ  
下一步我也還沒想好怎麼做，之前有看到 [rucc](https://github.com/maekawatoshiki/rucc) 的專案，
直接使用 rust 跟 LLVM 組合的套件，把剖析的程式碼直接轉成 LLVM IR，也許可以參考這種做法也說不定。  