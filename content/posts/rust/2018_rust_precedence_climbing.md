---
title: "使用 procedence climbing 正確處理運算子優先順序"
date: 2018-05-10
categories:
- rust
tags:
- rust
series: null
---

[上一篇]({{< relref "2018_rust_pest_PEG.md">}})我們說完如何用 Rust 的 PEG 套件 pest 生成簡單的程式碼分析器，但其實還有一些沒有解決的問題，像是 1 * 2 + 3 * 4 = 20，這是因為我們在處理 expression 時沒有處理運算子優先次序，只是從左到右掃過一遍。  
真正的 parsing 要考慮運算子優先權跟括號等等，例如：  
```
1 + 2 + 3 -> ((1 + 2) + 3) : Left associative（左相依）  
1 + 2 * 3 -> (1 + (2 * 3)) : * 優先權高於 +  
2 ^ 3 ^ 4 -> (2 ^ (3 ^ 4)) : Right associative（右相依）  
```

在這裡我們要介紹 precedence climbing 這套演算法，假設我們已經有了 Term (op Term)* 這樣的序列，現在要將它 parse 成 syntax tree，
可以參考[這篇的內容](https://eli.thegreenplace.net/2012/08/02/parsing-expressions-by-precedence-climbing)：  
<!--more-->

precedence climbing 其實不難，首先我們會先讀進一個 token 作為 lhs token，優先權為 0。  
接著持續取得下一個 operator 的優先權和 associative，如果運算子優先權 >= 目前優先權，則：  

* right associative，以同樣的優先權，遞迴呼叫 parse。  
* left associative ，則以高一級的優先權遞迴呼叫 parse。  

虛擬碼大概如下：  
```python
climb (min_precedence)
  lhs = get_token()
  while next_op precedence >= min_precedence
    op associative is left:
      next_precedence = min_precedence + 1
    op associative is right:
      next_precedence = min_precedence
    rhs = climb (next_precedence)
    lhs = op (lhs, rhs)

  return lhs
```

來個簡單的範例：如果所有運算子都是 left associative 、同樣優先權，例如 1+2+3+4，lhs 剖析出 1 之後，以高一級的優先權呼叫 climb，
所有遞迴呼叫的 climb 都不會進到 while，而是直接回傳剖析到的第一個 token 給第一次呼叫 climb 的 while loop 作為 rhs， parse 成 (((1+2)+3)+4)。  
如果是遇到更高權限的運算子，則呼叫的 climb 會進到 while loop ，把後面的 token 都消耗掉再回傳其 lhs，可能因為這樣因此取名為 precedence climbing。  

當然，比起我們自己實作，pest 裡面已經幫我們實作好了，只是在文件裡面都沒有提及，我也是看了用 [huia-parser](https://gitlab.com/huia-lang/huia-compiler)
這個用 pest 作 parsing 的 project ，才知道原來有這個功能可以用。  

廢話不多說直接來寫，首先我們要在 Project 中引入 pest 的 precedence climbing 實作：  
```rust
use pest::prec_climber::{Assoc, PrecClimber, Operator};
```
我們需要建好一個 PrecClimber 的物件，這個物件會儲存一個 Operator 的 Vec，優先權依順序增加，
如果有相同優先權的運算子，則用 | 連接，每個 Operator 中會保存 parser 中定義的 Rule 跟 Assoc::Left 或 Assoc::Right，
例如我們的 simple 的定義（這裡我加上一個 op\_sub 來示範 | 的用法）：  
```rust
let PREC_CLIMBER = PrecClimber::new(vec![
    Operator::new(Rule::op_lt,  Assoc::Left),
    Operator::new(Rule::op_add, Assoc::Left) | Operator::new(Rule::op_sub, Assoc::Left),
    Operator::new(Rule::op_mul, Assoc::Left)
])
```

要剖析的時候則是呼叫 PrecClimber 的 climb 函式，它的型態乍看之下有點複雜：  
```rust
pub fn climb<'i, P, F, G, T>(&self, mut pairs: P, mut primary: F, mut infix: G) -> T
where
    P: Iterator<Item = Pair<'i, R>>,
    F: FnMut(Pair<'i, R>) -> T,
    G: FnMut(T, Pair<'i, R>, T) -> T
```

其實也不難理解，它只是將上面的 precedence climbing 虛擬化為幾個函式：  

* pairs: P 是全部要走訪的 (term (op term)*) iterator。  
* primary: F 會吃一個 term 將它轉為剖析後的結果。  
* infix: G 為結合方式，拿到兩個剖析後的結果跟一個運算子，將兩個結合起來。  

這裡的 primary 其實就是我們寫過的 build\_factor：  
```rust
fn build_factor(pair: Pair<Rule>) -> Box<Node> {
    match pair.as_rule() {
        Rule::variable => Node::variable(pair.into_span().as_str()),
        Rule::number => Node::number(pair.into_span().as_str().parse::<i64>().unwrap()),
        _ => unreachable!(),
    }
}
```

infix\_rule 其實也只是把我們之前 build\_expr 的東西給取出來：  
```rust
fn infix_rule(lhs: Box<Node>, pair: Pair<Rule>, rhs: Box<Node>) -> Box<Node> {
    match pair.as_rule() {
        Rule::op_add => Node::add(lhs, rhs),
        Rule::op_mul => Node::multiply(lhs, rhs),
        Rule::op_lt => Node::lessthan(lhs, rhs),
        _ => unreachable!(),
    }
}
```

build\_factor 會吃進 token，將它轉為我們 AST 的型態 `Box<Node>`；
infix\_rule  使用 climb ，當我們拿到一個 expression token，要做的就只剩下把它丟給 climb 去爬，into\_inner 將 expression token 轉為下層的 token iterator：  
```rust
// pair.as_rule() == Rule::expr
pub fn climb(pair: Pair<Rule>) -> Box<Node> {
    PREC_CLIMBER.climb(pair.into_inner(), build_factor, infix_rule)
}
```
:
最後一小步，我們想要避免每次要 climb 的時候，還要重新產生 PREC\_CLIMBER 這個物件，反正語法固定之前 PREC\_CLIMBER 沒理由會變動，因此我們用了 lazy\_static 這個套件，將它變成 static 的物件：  
```rust
#[macro_use]
extern crate lazy_static;

lazy_static! {
    static ref PREC_CLIMBER: PrecClimber<Rule> = build_precedence_climber();
}
fn build_precedence_climber() -> PrecClimber<Rule> {
    PrecClimber::new(vec![
        Operator::new(Rule::op_lt,  Assoc::Left),
        Operator::new(Rule::op_add, Assoc::Left),
        Operator::new(Rule::op_mul, Assoc::Left)
    ])
}
```

這麼一來我們的 simple 剖析器就完成了，現在 1 * 2 + 3 * 4 會是正確的 14 了，可喜可賀可喜可賀。