---
title: "整理 rust module 的安排方式"
date: 2018-04-06
categories:
- rust
tags:
- rust
- module
- understanding computation
series: null
---

故事是這樣子的，兩年前因為傳說中的 jserv 大神的推薦，我讀了 [Understanding Computation 這本書](http://computationbook.com/)，讀完覺得學到很多東西，深受啟發；
後來大概花了兩個月的時間，用Rust 重寫了裡面所有的範例程式碼，目前在 github 上查了一下，
我應該是除了[原作實作](https://github.com/tomstuart/computationbook)之外，實作最完整的一個，可謂一人之下，萬人之上（誤。  

最近因為一些原因，把之前的實作打開來看，馬上關上，假的！趕快在筆電前面打坐。  
當初到底怎麼寫這麼醜，還查到有些章節的內容沒有實作完，那時候可能太難不會寫，先跳過結果就忘了QQ……最近這一兩個禮拜陸續花了一點時間整理。  

這次整理的一大修正，是把本來是散在各處的原始碼，重新照 rust 慣例統整到 src 資料夾下面，並使用 cargo 管理，帶來的好處包括有：

1. 可以一次 cargo build 編譯所有程式
2. 引入 cargo test 代替本來編譯成執行檔用 println debug 的實作
3. 在各章的內容間重用 module ，提升重用比例
4. 另外也能使用網路上其他人寫的 Rust module（其實這才是原初整理的目的）  

例如在我之前實作的程式碼，在寫 finite automata 時，dfa, nfa 各自有一個實作，使用 u32 作為狀態；
但到了 regular expression 的時候，為了產生 nfa 就不能用 u32 作為狀態，於是我複製了一版 nfa，
[改成用 object pointer 作為狀態]({{< relref "2016_rust_re.md">}})，
兩者程式碼的重複率就非常高，這次也一併改成 generic 的 nfa 實作，兩邊就能分享同一套程式碼。  
<!--more-->

本來以為整理就是把程式碼搬一搬，也差不多就結束了，結果不是（當然有一部分是我自己蠢），但也是因為這個機會，弄懂的 Rust 的 module 系統，這裡作個記錄。  

在一個 rust project 當中，最重要的都放在 src 資料夾下面，包括要編成函式庫或執行檔的原始碼都在這裡，
其他像編譯結果的 target、文件的 doc、測試的 test ，相對來說比較沒這麼重要（好啦還是很重要，只是不是本文要討論的重點）。  

rust 的編譯是由 cargo.toml 所驅動，一個 rust 模組只能編出一個 rlib，由 cargo.toml 的 [lib] 所指定，例如我這個專案指定 library 名稱跟路徑如下：  
```toml
[lib]  
name = "computationbook"  
path = "src/lib.rs"
```
如果不設定的話，cargo 會預設編譯 src/lib.rs，並自動從資料夾名稱產生 library 名稱；這個 library 名稱非常重要，先把它記著。  

函式庫的實作就在 lib.rs 裡面，包含函式庫所有的函式，可以加上 pub 讓外界可以取用；當函式多的時候，就開始需要幫他們分門別類，也就是 rust 的 module：  
```rust
fn libraryfun () {}
mod modulename {
    fn libraryfun () {}
}
```
用起來有點像 C++ 的 namespace，上面例子中，兩個 libraryfun 是不會衝突，一個是 libraryfun，一個是 modulename::libraryfun。  
然後 Rust 以它預設什麼都不開放的嚴謹著稱，上面的不寫 pub mod，pub fn 的話，外面是無法取用的。  

函式更多，可以把整個 module 移到另一個檔案，lib.rs 裡面只留下 mod 宣告：  
```rust
mod modulename;
```
內容移到 modulename.rs 裡面。  
或者有足以獨立出來的功能，可以放到 modulename 資料夾下，並加上 modulenmae/mod.rs 來表示這個資料夾是一個 module。  

module 大致的規則就是這樣  
1. 可直接在檔案內定義。  
2. 只寫 mod modulename，內容放在其他檔案。  
3. 只寫 mod modulename，內容放在同名且內含 mod.rs 的資料夾內。  

注意第二、三個方法互相衝突的，不能有 mymodule.rs 跟 mymodule/mod.rs 同時存在，rust 會跳出編譯錯誤。  
另外有一個特例是在 src 下，只有 lib.rs 有權限宣告 submodule，例如 lib.rs 宣告一個叫 network 的 module 並把內容放在 src/network.rs，network.rs 就不能再宣告它有一個 module server。  
```rust
// src/lib.rs  
mod network;  

// src/network.rs  
mod server; // compile error
```
這裡的 error 訊息很詭異，是 
```txt
file not found for module 'server'
```
但初遇時覺得見鬼，檔案就在那邊你跟我說沒有…。  

正確作法是把 network.rs 移到 network 資料夾中，改名為 mod.rs 指明這個資料夾下有哪些 module，這時候 src/lib.rs 裡面的 mod network; 就會指向 network/mod.rs 裡寫的 mod；
把 server.rs 放在network 資料夾中，就適用上述的規則二，在 mod.rs 裡只寫 mod server;，內容放在其他檔案。  

講完 module 的定義，現在可以來講引用，這部分要分成兩種，一是 src 下函式庫的引用：  
上面第三種規則的，拿我的 dfa module 為例， mod.rs 定義了 dfarulebook.rs 跟 dfa.rs ，dfa 需要 dfarulebook，因為他們都在 dfa module 內，要引用時就用：  
```rust
use super::dfarulebook::{DFARulebook};
```
因為這些檔案不太可能會分開，用 super 的好處是無論 dfa 資料夾到哪這個參照都不會變；
在 mod.rs 裡面實作測試的 module 也是一樣，測試當然需要原本 module 裡的東西，這個時候也是使用 super：   

```rust
mod dfarulebook;
#[cfg(test)]
mod tests {
use super::dfarulebook::{DFARulebook};
}
```
同樣是第三種規則的 mod.rs，mod.rs 本身就是 dfa module，它需要用到 dfarulebook.rs 的內容，則是：  
```rust
mod dfarulebook;
mod dfa;
use self::dfarulebook::{DFARulebook};
```
來自 dfa 之外的引用就要用完整路徑，從 src 開始一路指定：  
```rust
use the_simplest_computer::dfa::dfarulebook::{DFARulebook};
```
你可以想像，從 src/lib.rs 開始，要可以透過一連串的 mod.rs 找到我們要的 module；上面的 lib.rs 裡就有 mod the\_simplest\_computer; ；the\_simplest\_computer/mod.rs 裡有 mod dfa; 一路像串棕子一樣把各模組串起來，如果有地方沒串好，cargo 就會回報錯誤。  

再來是執行檔，這裡我也是試好久才試出來。  
現在的 cargo 可以在 Cargo.toml 裡面，用 [[bin]] 欄位指定多個執行檔目標，不然就是預設的 src/main.rs，這跟 library 不同，一個 Cargo.toml 就只能有一個 [lib] 目標。  
這裡關鍵的點就是：**執行檔不是 library 的一部分**，cargo 先從 lib.rs 編譯出函式庫，然後編譯執行檔跟函式庫做連結；
執行檔要用編譯的函式庫，就要先宣告 extern crate，然後每層 use 都在前面多加上函式庫，上面說要記著的函式庫名稱就是這裡要用到：  

```rust
extern crate computationbook;
use computationbook::the_simplest_computer::dfa::dfarulebook::{DFARulebook};
```
超級長對吧XD  

如果函式庫名稱是 cargo 自動產生，可以去 target/debug/ 看它編譯出什麼，我上面的例子就是：`libcomputationbook.rlib`  

故事大概就到這裡，這次總算弄懂 cargo 如何管理各 module 了，感謝大家收看。  

在這裡就雷一下大家，下一篇就要來說一下，本來整理這個 project 要做的東西，估計會是一篇理論跟實作兼具的文章，敬請期待。  

## 本文之完成，感謝以下參考資料：  
[Cargo guide](https://doc.rust-lang.org/cargo/guide/)  
[Rust module guide](https://doc.rust-lang.org/book/second-edition/ch07-01-mod-and-the-filesystem.html)  
[minisat-rust 專案](https://github.com/mishun/minisat-rust)，因為它編得過我編不過，它的複雜度又剛剛好夠複雜，就拿來研究了一番