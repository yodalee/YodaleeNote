---
title: "有關 Rust test 的那些奇奇怪怪的東西"
date: 2018-07-14
categories:
- rust
tags:
- rust
series: null
---

有關 Rust test 的那些奇奇怪怪的東西  
最近因為在寫 Rust code，想到那句朗朗上口的口號「原碼未動，測試先行」，想說就來寫點測試，嘗試一下傳說中的 TDD 開發，~~連路上的計程車也愈來愈多 TDD 了你還不 TDD~~。  
想說就來整理一下 Rust 測試相關的編排，還有我遇到那堆奇奇怪怪的開發經驗。  
簡而言之，我們先放掉什麼把 test 寫在 comment 裡面的設計，那東西我至今沒用過也不太看人用過，~~註解跟文件什麼的只是裝飾而已，上面的大人物是不會懂的~~。  
<!--more-->

我們只看兩個：單元測試跟整合測試。  

在 rust 裡面單元測試直接跟程式碼寫在一起，通常是在一個模組的 mod.rs 裡，或者是 lib.rs 裡，
要寫在一般的原始碼裡面也可以，但通常到模組層級才會開始寫測試，有關 rust 模組的架構就請參考[拙作]({{< relref "2018_rust_module.md">}})。  

寫測試的時候首先先加上測試的模組，裡面加上測試用的函式：  
```rust
#[cfg(test)]
mod tests {
  use super::*;

  // test rule can match content exactly
  fn can_parse(rule: Rule, content: &str) -> bool {
    match CParser::parse(rule, content) {
      Err(_) => false,
        Ok(mut pair) => {
          let parse_str = pair.next().unwrap().into_span().as_str();
          println!("{:?} match {}", rule, parse_str);
          parse_str == content
        },
    }
  }

  #[test]
  fn test_identifier() {
    assert!(can_parse(Rule::identifier, "a123_"));
    assert!(!can_parse(Rule::identifier, "123"));
    assert!(can_parse(Rule::identifier, "_039"));
  }
}
```

#[cfg(test)] 宣告這是測試用的模組，只有用 cargo test 才會執行，呼叫 cargo build 並不會編譯測試模組。  
測試模組為被測試模組的子模組，地位就如同其他被測試模組中的檔案一樣，如果呼叫被測試模組中的原始碼，使用 super 來到被測試模組的位置，再向下 use 其他檔案即可。  
不過測試模組有一些特別的權限，一般來說不加 pub 的函式都是 private ，在其他檔案無法呼叫，唯有測試模組可以。  
再來就是盡情地寫測試，測試的函式要用 #[test] 標註，模組中也可以加上不是測試用的輔助函式，就如上文中的 can\_parse。  
初次寫的時候一定會覺得 #[cfg(test)] 跟 #[test] 有夠難打，一定要加進編輯器的自動補齊裡面。  

Rust 的整合測試位在整個模組之外，呼叫模組的函式時，就跟所有使用你模組的人一樣，也只能呼叫公開的函式。  
這個功能我到現在還沒用過，畢竟我還沒寫出一個完整的模組過XDD  

總而言之，我們在 src 資料夾之外建立一個 tests 資料夾，在這個資料夾裡面的所有原始碼都會是測試用的原始碼，
每個檔案都會單獨進行編譯，這裡也不需要指定 #[cfg(test)]，全部預設就是測試的原始碼。  
要使用原本的模組必須用 extern crate 的方式引入，然後直接在 use 的時候，從整個函式庫的名字完整的打出來。  
在 tests 裡面的測試也可以分門別類，建立測試的模組跟測試前設定的函式，不過我都還沒用過所以這裡就不多說了。  

要執行測試，只需要使用 cargo test 即可，另外這裡有一些很常用的變體：  

* cargo test -- --test-threads=1  
使用一個執行緒進行測試，讓測試的結果不會交錯輸出。  

* cargo test -- --nocapture  
測試正常來說會把所有寫到 stdout 的內容全部截下來，普通是看不到的，測試失敗才會將該測試的內容印出；
如果平常就想看到測試印出的內容，就要加上 --nocapture 選項；要注意的 cargo test 一定會把輸出到 stderr 的內容截下來，
沒有什麼方法可以讓它吐出內容，所以測試裡唯一能用的只有 println。  

* cargo test <keyword>  
測試很多的時候也許只會想跑其中某些測試，這時可以下 keyword，只有測試名稱包含keyword 的測試才會執行，當然以函式名稱直接當作皮我就會執行一個測試了。  

* cargo test -- --ignored
測試可以加上 #[ignore] 標註這個測試現在還不用跑，下命令的時候可以加上 --ignored 來強制執行這些測試。  
不過我猜一般人測試都不會多到需要這個功能（或者說大家加測試的時候通常都是 code 寫完了，「原碼未到、測試先行」的狀況反而比較少）。  

其實綜觀上面這幾個設定，多少可以看到一些測試設計上的準則，例如要能夠平行不相依，測試不管輸出，原則上所有測試都要通過，加 ignore 是非不得已等等；不過管他測試怎麼寫，能測出錯誤的就是好測試。  

本篇文章內容主要來自 [rust doc 的 testing](https://doc.rust-lang.org/book/second-edition/ch11-00-testing.html)  