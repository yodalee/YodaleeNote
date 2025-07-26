---
title: "Rust Pointer, Ownership and Lifetime"
date: 2015-03-01
categories:
- rust
tags:
- rust
- ownership
- lifetime
series: null
---


這篇[主要參考](http://slides.com/liigo/rust-memory/fullscreen#/)  

## 前言：

pointer是語言上一種常見的實作方法，也是C/Cpp常見的寫法，讓你可以利用指標對資料(某塊記憶體)進行操作，達到極高的操控性。  
問題是什麼呢？Pointer 讓你直接操控一塊記憶體，相對的，它也會造成空的指標，雙重釋放、未釋放記憶體等不安全
（這裡的安全是指不正常的使用指標，造成memory leak）的操作；
兩個指標可以指向同一塊記憶體，在多執行緖裡造成race condition(競態條件)。  

**我們既需要pointer 所帶來的彈性，又不希望pointer 和不正常使用帶來的不安全。**  

同時當系統愈來愈大，加上更多平行化機制之後，要求設計師對每塊宣告的記憶體負責愈顯得不切實際，
作為下一代的語言實在不該讓程式莫名的存取到不該用的記憶體，讓作業系統丟出seg fault 把程式切掉(引用：AZ大神)。  
類似的問題與回應在Cpp也看得到（我真懷疑Cpp到底有什麼概念沒實作的XDDDD），像是 C++11引入的smart pointer, shared pointer，都是針對這個問題而來。  
<!--more-->

Rust 使用的解法是：定義了Rust Ownership跟Lifetime規則，直接限制pointer 的傳遞、複製、刪除，由編譯器在編譯時即進行檢查（老實說還滿嚴格的 Jizz），避免不正當的pointer 使用方式，來兼顧安全與控制；同時排除掉執行期的檢查成本。  
相對於golang，使用的是garbage collection 的方式來處理資源釋放的問題，Rust 連garbage collection 都不要有，一但你的資源(memory) 生命期結束，編譯器就自動幫你把資源釋放掉。  

## Pointer, Ownership, Lifetime:

首先我們先介紹Rust 的pointer，主要有兩種型式，一種是直接的Reference，就跟C/C++一樣，可以用 & 或是 ref 取另一個變數的位址；
另一種則是box pointer，跟C/C++的malloc 一樣，它會分配heap 區內的記憶體給這個pointer，使用方法請見：  
* [Ref pointer](https://doc.rust-lang.org/stable/rust-by-example/scope/lifetime/static_lifetime.html)
* [Box](https://doc.rust-lang.org/stable/rust-by-example/std/box.html)

我們這裡提到兩個名詞：持有權(Ownership)跟生命期(Lifetime)，就來做細部介紹：  

## Ownership

Ownership指的是一個pointer 對某塊記憶體的持有權。  
例如在ownership guide 裡的例子，在一個scope 裡面malloc/free 一塊記憶體，在Rust 裡就是直接宣告let x = box; Rust compiler 會幫你放掉這塊記憶體。  
所有的資源都只能有一個持有者，擁有持有權的pointer 可以將pointer 轉送(Move)或借給(Borrow)其他人，例如把它傳送到函數裡面，當我們把pointer 當做函數的argument時，資源擁有權就轉走了。  
例如當我們用box pointer：也就是C裡面的malloc/free 型態的pointer，傳送到function 裡的時候，在caller 的變數即無法再存取這塊資料，在函式的末端，這個資源的持有權無人承接，系統就將它釋放掉，就像這樣：  
```rust
fn main() {
    let x = Box::new(5);
    add_one(x);
    println!("{}", x);
}

fn add_one(mut num: Box<i32>) {
    *num += 1;
}
```
上面的println 會出現compile error，因為資源已經轉手給 `add_one`，並在 `add_one` 的末端被釋放掉，由於main裡的pointer 已經無法再存取那塊記憶體，由此杜絕存取dangling pointer 的可能性。  

如果要再使用這塊記憶體，就要在函數末端將它的擁有權傳回來  
```rust
fn add_one(mut num: Box<i32>) -> Box<i32> {
    *num += 1;
    num
}
```
這個寫法相當常見，在Rust 裡可以用ref 的寫法來代替，這在文件內稱為借用(Borrowing)，就像這樣：  
```rust
fn add_one(num: &mut i32) {
    *num += 1;
}
```

## lifetime

那Lifetime呢？在Rust 裡每個變數都有它的Lifetime，一般來說Rust compile 會幫你把這些都管好，你想寫明的時候才用<'name>來指明。  
下列兩者其實是等價，只是一個寫明Lifetime 的名字：  
```rust
fn add_one<'a>(num: &'a int) -> int {
    *num + 1
}
fn add_one(num: & int) -> int {
    *num + 1
}
```
同時Lifetime 的範圍其實也沒那麼不好懂，大抵上就是scope，一但資源出了scope，未使用的就會被釋放掉。  

## 結語：

Pointer, ownership, lifetime 其實是Rust 不太好搞懂的觀念，其實它就是由編譯器進行嚴格檢查，限制不當使用的C pointer。
我的感想是，一但設計師適應這樣嚴格檢查，在程式設計階段自然就排除掉C/C++高自由度帶來的那些：可以但是不應該這樣寫的不安全寫法了。  

## 參考資料：

[Rust By Example Scoping](https://doc.rust-lang.org/stable/rust-by-example/scope.html)