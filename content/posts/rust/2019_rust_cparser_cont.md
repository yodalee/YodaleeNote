---
title: "用 PEG 寫一個 C parser 續"
date: 2019-01-06
categories:
- rust
tags:
- c
- rust
- parsing expression grammar
series: null
---

自從去年十月把 nixie tube clock 完工之後，好像都在耍廢之類的，結果 11/12 月兩個月都沒有發文，
其實這兩個月裡面，有的時間都在改之前寫的 [C parser]({{< relref "2018_rust_cparser.md">}})，
其實整體完成度愈來愈高了，今天發個文來整理一下到底做了啥。  
這次做了幾個改變，主要的修正就是加上 expression, declaration, statment 的處理，也學到不少東西，這裡一一列一下：  
<!--more-->

## macro

這是要對應之前寫的 parse\_fail。  
本來 parse\_fail 的用意，就是在剖析出錯的時候，把程式終結掉，然後丟一點錯誤訊息出來；本來我的實作是一個函式，利用 unreachable! 丟出錯誤：  
```rust
fn parse_fail(pair: Pair<Rule>) -> ! {
  let rule = pair.as_rule();
  let s = pair.into_span().as_str();
  unreachable!("unexpected rule {:?} with content {}", rule, s)
}
```
這樣的實作會有個問題，在程式終止之後的位置一律都會在 parse\_fail 這個函式裡，而不是真正出錯的剖析函式，要除錯必須開 stack trace 才能做到。  

為了避免這個狀況，我們改用 macro 實作 parse\_fail，這樣 unreachable! 就會在出錯的位置展開，在終止程式的時候給出正確的位置。  
關於 macro 小弟在很早的時候有寫過一篇[貧乏的介紹文]({{< relref "2015_rust_macro.md">}})，
改起來也很簡單，把原本作為函式參數傳進來的 pair，由 macro 的 $x:expr 取代，然後用 $x 取代本來 code 裡面所有的 pair，如下：  
```rust
macro_rules! parse_fail {
  ( $x:expr ) => {
    {
      let rule = $x.as_rule();
      let s = $x.into_span().as_str();
      unreachable!("unexpected rule {:?} with content {}", rule, s)
    }
  }
}
```
這樣所有程式裡的 parse\_fail(pair) 就會自動開展成。  
```rust
let rule = pair.as_rule();
let s = pair.into_span().as_str();
unreachable!("unexpected rule {:?} with content {}", rule, s)
```

另外有一個要注意的是，假設我 parse\_fail 的 macro 寫在模組的 helper.rs 裡面，那麼在寫模組的 lib.rs 時，
mod helper 要在所有其他 mod 之前，並加上 #[macro\_use] 修飾，這跟 rust 模組的編譯流程有關。  
macro 是跟順序有關的，在 mod helper 之後這個 parse\_fail 的 macro 才有定義，後面的 mod 才能使用這個 macro，詳細可以[參考這篇](https://danielkeep.github.io/quick-intro-to-macros.html#some-more-gotchas)。  

如果想讓使用 extern crate 的人也能使用這個 macro，就要在定義 macro 的時候在前面加上 `#[macro_export]` 的標籤，每個 macro 都需要單獨 export 才行。  

## 處理 expression 的正確姿勢：

如果有看上一篇，會看到我用 PEG 套件 pest 的 precedence climbing 的功能來完成對 expression 的剖析，但其實那是不完整的，
原因在於我們把的做法是把 expression 直接導向 `unary_expr (op_binary unary_expr)*` 的組合，這樣我們看到 expression，
把它展開來就可以得到一大串 `unary_expr` 跟 `op_binary` 交錯的序列，把這串東西丟進 precedence climbing 裡面就能建好 expression tree 了。  

但實際上的 C 語言比這還要複雜，expression 下面還有 assignment expression，conditional expression 等等，這些 expression 是必須存在的，
例如在變數 decl 的地方就會需要 assignment expression，我們本來的寫法把 assignment expression 等等都抹掉了要怎麼辦？
把它們加回去要怎麼讓本來的 precedence climbing 的 code 還能正確運作？  

後來發現的正確處理方法是這樣的，在文法的部分要把 assignment expression 等東西加回去，裡面用到的三元運算子 ?: ，assignment operator =, +=, -= 等等都從 op\_binary 裡面排除，像是這樣：  
```txt
logicalOR_expr = _{ unary_expr ~ (op_binary ~ unary_expr)* }
conditional_expr = _{ logicalOR_expr ~ ( op_qmark ~ silent_expression ~ op_colon ~ conditional_expr)? }
assignment_expr = _{ (unary_expr ~ op_assign)* ~ conditional_expr }
silent_expression = _{ assignment_expr ~ (op_comma ~ assignment_expr)* }
expression = { assignment_expr ~ (op_comma ~ assignment_expr)* }
```
原本的 expression 現在只剩 logicalOR\_expr，其他的都要拉出來自立條目，讓其他的文法如 declaration 能使用它，但同時都使用 \_{} 讓剖析後他們不會吐一個 node 出來，這樣看到 expression 之後，展開來仍然是一串 unary\_expr 跟 operator 交錯的序列。  

這樣做的好處是 precedence climbing 仍然可以沿用，所有的 operator 都算在 expression 頭下，壞處是我們必須依文法去調整一些文法要不要吐出 node，現在的實作在有兩個特例：  
一個是如上面所示，conditional expression 的規定是 logical\_OR\_expression ? expression : conditional\_expression，有一個 expression 在裡面，這會違反我們的假設：把 expression 展開來看都會是 unary\_expr 跟 operator 的組合，因此我們要加上一個特別的 silent\_expression 在剖析完之後不會生成 expression node ，而是完全展開。  

另一個剛好是反過來的狀況，在 C 的 initializer 文法（6.7.9）是這樣定的：  
```txt
initializer -> assignment_expression | "{" initializer-list "}"
```
但…我們的 assignment\_expression 是不存在的，如果 initializer 真的剖析為 assignment\_expression，
展開 initializer 只會得到「一團 unary\_expr 跟 operator 的組合」，會跟 initiailizer-list 搞在一起，所以反過來我新增了一個 initializer\_expr，把 assignment expression 封起來：  
```txt
initializer_expr -> assignment_expression
initializer -> initializer_expr | "{" initializer-list "}"
```
這樣拿到 initializer 就能放心展開，再看內容物是 initializer\_expr 或 initializer-list 來決定下一步，
如果是 initializer\_expr 就能放心的丟給 precedence climbing 去建 expression 了。  

上面兩個例子都沒什麼道理可言，基本上就是見招拆招，大致就是兩條好像在說廢話的規則：  

1. 會展開的 rule 裡面出現這團 rule 的開頭，則開頭的 rule 代換成自動展開的版本。
2. 會展開的 rule 跟其他 rule 並列，要再多包一層不會展開的版本。

## ! tag for = and ==

在這次修改之前都沒什麼機會用到 ! tag，也就是 PEG 裡的 Not predicate，這次在處理更複雜的 expression 遇到，
某些狀況 = 的優先權高過 == 以致 == 先被剖析成 = 了。  
這時候 op\_assign\_eq 就要改為：  
```txt
op_assign_eq = { "=" ~ !"=" }
```
來確保 = 之後沒有接著其他的 =。  

## comment

```txt
comment = _{ "/*" ~ (!"*/" ~ any)* ~ "*/" | "//" ~ (!"\n" ~ any)* ~ "\n" }
```
comment 也是這次的修改之一，同樣利用了 ! 的特性，上面兩條其實都滿直覺的：  
開頭是 /* ，再來只要不是 */ 的內容，就可以匹配任何字元；開頭是 // 再來只要不是換行就可以匹配任何字元。  
這兩個例子都使用了 Not predicate，功能很類似 C 裡面的 peek，偷看一下後面的東西而不消耗任何東西。  

## Hidden grammar:

這點比較不是程式的問題，而是 C 規格的問題，注意以下這些都符合 C grammar，但在工作上千萬別這麼寫，大概有十成的機率你會被電到[天上飛](https://www.youtube.com/watch?v=qTQkaDoeaGQ)。  

* volatile, restrict, const 隨便加，加幾個都沒關係
* 其實可以不用 type，這是符合文法的，gcc 在這裡會直接給你一個 int。
* 也可以宣告型別，儲存類型什麼的，最後…沒變數。

所以可以寫像是：  
```c
int const volatile const volatile const volatile const volatile const volatile const;
const * restrict restrict restrict a;
```
說真的，看到這樣寫 code 我也會把人電到天上飛，其實我也不知道為什麼 C grammar 要允許這樣的文法就是，看到 gcc 編譯過我差點笑死。  

現在離大致完成還有一個最大的難關，就是 declaration 那邊還有 struct, union, enum 等著處理，文法上是還好，更大的問題是不知道怎麼寫轉出來的 AST，
之前我大部分都參考強者我學長 suhorng 大大的 haskell 實作，或者參考一些 LLVM 的 IR 實作…當然是沒辦法到 LLVM 那麼複雜啦QQ。  

總之最近進度嚴重卡關，這才是我為什麼在這裡打住寫篇文的原因（誒。  

自己自幹 AST，配上最近工作上做的一些改動，讓我有了下面這個體會：  
資訊源自於數學，本身是無窮的，正如數線上有無數的正整數，無窮的有理數，比無窮更無窮的無理數；數學這個「概念」本身就有無限的資訊  
但有了電腦一切就不一樣了，我們只有有限的位元能夠近似數學的概念，所以就有了取捨。  
用 64 位元可以表示到 18446744073709551615，大約是 10^19，於是 10^19 -> ∞ 的資訊就被捨去了；同理我們決定浮點數用 IEEE 754 表示，有些小數就是無法表示，無窮的資訊對上有限資源，其間的差距令人絕望。  

就如我們把 C code parse 成 AST，AST 裡面要保留多少資訊？  
像我這樣基本上只保留了簡單的 AST node，隨便建顆樹而已；LLVM 的 IR 就是許多嚴僅設計的物件，保留程式語言的繼承關係跟內部的屬性設計，在處理上就有更多能運用的資訊。  
工作上需要的是用電腦處理幾何的資訊，像是點、線、四邊形，那麼一個線段的物件要儲存什麼資訊？  
可以用起點終點來表示一條線，基於效率跟空間考量，我們可能可以存一下線段是不是垂直的、水平、甚至是不是斜上跟斜下，
但要不要存一個 double 的斜率呢？這就要看平常是不是很常需要算斜率了。  
存更多的東西自然可以方便做些處理，但線段更新時也要更新更多的資訊。  

捨去是面對資訊時的必要，**資訊工程處理的問題一直都不是資訊太少而是資訊太多**，而要捨去什麼資訊、保留什麼，這不是科學而是技藝，
這些都不是數學，不會有一個標準的答案，而是視需求去選擇，需要經驗、工具、模擬、除錯、測試……用實驗跟說理得到一個最佳近似的解。  

正如大學學系的名字：資訊<工程>學系。  