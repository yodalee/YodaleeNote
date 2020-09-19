---
title: "Rust 遞迴結構 recursive structure"
date: 2016-03-23
categories:
- rust
tags:
- rust
- understanding computation
series: null
---

之前實作Computation book的範例程式碼，一直卡關的第2章原始碼解析的部分，最近突然有了大幅的進展
(因為在網路上找到一個別人寫好的相關原始碼)，讓我突然頓悟rust 相關的設計，這裡解釋一些常用的技巧。  
<!--more-->

在建tree的部分，C++ 可能會定義介面用的base class ，再定義下面的derived class，這樣就能用base class 作為介面建tree，
Rust 中我們可以用enum 做到這點，enum 除了像C like 的用法，也能指向物件，內含匿名或是有名的物件，我在這裡都是用匿名物件來實作：  
<https://doc.rust-lang.org/book/enums.html>  
```rust
#[derive(Clone)]
pub enum Node {
    Number(i64),
    Add(Box<node>, Box<node>),
    Multiply(Box<node>, Box<node>),
    Boolean(bool),
    LessThan(Box<node>, Box<node>),
    Variable(String),
    DoNothing,
    Assign(String, Box<node>),
    If(Box<node>, Box<node>, Box<node>),
    Sequence(Box<node>, Box<node>),
    While(Box<node>, Box<node>),
}
```
之所以要Box<Node> 而不是Node，在rustc --explain E0072 中有介紹，大體是recursive structure 裡，子物件若要包含父物件，
一定要是Box 或是Reference &，否則程式算不出Node 需要多大。  

用了enum 之後，其他function 的實作也就是在enum 上實作，並用match 來處理所有enum 可能出現的結果，例如我的reducible() 實作：  
```rust
fn reducible(&self) -> bool {
    match *self {
        Node::Number(_) | Node::Boolean(_) | Node::DoNothing => false,
        _ => true,
    }
}
```

reduce 的實作則是：

```rust
fn reduce(&self, environment: &mut Environment) -> Box<Node> {
    match *self {
        Node::Add(ref l, ref r) => {
            if l.reducible() {
                Node::add(l.reduce(environment), r.clone())
            } else if r.reducible() {
                Node::add(l.clone(), r.reduce(environment))
            } else {
                Node::number(l.value() + r.value())
            }
        }
    }
}
```

> ……reduce會將原本的node 替換掉，只能用self 當參數（好其實是我用&self就會出一些很詭異的錯誤，我還不知道怎麼解）

注意這邊的 match 裡要寫 `ref l, ref r`。
如果寫 `Node::Add(l, r)` ，這樣的意思是，如果我們 match Add，裡面的 l, r 的所有權**有可能**會被轉移掉，例如
```rust
return l
```
或是
```rust
return Box<l>
```
function 又是寫 `reduce(&self)` 的話，表示我self 是跟人用reference 借來的，我不能又把self的所有權又送出去，所以rustc 會警告match *self這行：  
```txt
cannot move out of borrowed content
```
即便你的code 沒有這麼做，rust 還是不允許這麼寫。  

`ref l, ref r` 表示我 l, r 仍然是借用，而借用的內容是傳不回去的，這樣一路從 self 下來都是借用，就沒有所有權轉移的問題；
要傳回一個跟 l 或 r 一樣的內容，就要在Node 的屬性加上`#[derive(Clone)]`，用 l.clone()複製一個新的物件，試圖去 dereference l 或 r (*l, *r) 同樣都會被 rust 拒絕。  

## 使用trait：  
在本來的範例中他是將程式碼分到不同的資料夾，並用
```ruby
require_relative '../syntax/add'
```
的方式來擴展原有的程式，Rust不允許使用在上層資料夾裡面的程式碼，我這裡是利用trait 來達成模組化的目的。  

Syntax.rs 中只定義AST 裡所需要的物件。  
其他的function 我們都用trait 來定義，如果我們要用small\_step 的reduce
```rust
use reduce::{Reduce}
```
裡面就實作相關的function，好處是若main不需要reduce 的功能，不要use 這個trait 即可。  

相關的原始碼可以看[這裡](https://github.com/yodalee/computationbook-rust/tree/master/src/the_meaning_of_programs/simple)