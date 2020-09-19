---
title: "Rust struct, impl, trait"
date: 2015-02-25
categories:
- rust
tags:
- rust
- struct
- trait
series: null
---

前言：最近被強者我同學呂行大神拉去寫[Servo](https://github.com/servo/servo)  
用的語言是 [Rust](http://www.rust-lang.org/)，是個非常年輕的語言(2012年出現)，另外有一個老一點的 Golang(2009)，基本上目前中文找不到什麼資料，就算是英文的文件本身也不太完整Orz  

想說文件這種東西，只要不是亂寫愈多愈好，就在這個blog 上寫一點Rust 相關的文件，等寫多了好整理起來；
基本的rust 像什麼函式怎麼宣告、if 格式之類我就不寫了，那個自己翻一翻就會了。  
我出身是C/C++, Python，所以解釋角度也比較偏這樣的語言。  

這篇介紹Rust裡的集合物件: Struct, impl 跟trait  
<!--more-->

struct在rust 裡跟C++/Python的class一樣，是物件的集合跟函式的集合，不過rust 採取的方式是用 struct A / impl A的方式，把集合的物件跟函式分開。  

所以在Rust 裡很常看到這樣的寫法：  
```rust
struct Car
{
    Speed: int
}

impl Car {
    fn run(&self){
        println!(“my speed is {:d}”, self.Speed);
    }
}
```
一個struct 比較像C裡的struct，補上impl 就變成C++裡面的Struct/Class  

同時如果我們要提供一個共同的介面(interface)呢？  
例如我要Car跟People都實作run 這個函式，在Rust 裡這東西可以用trait 來實作，
首先先實作trait，然後就可以對struct實作trait，這東西很像java 裡面的 interface，例如：   

```rust
trait movable {
    pub fn run(&self);
}

impl movable for Car{
    fn run(&self){
        println!(“my speed is {:d}”, self.Speed);
    }
}
```
之後就可以明目張膽(?)的呼叫Car.run()了  

更多內容請見：  
<https://doc.rust-lang.org/stable/rust-by-example/trait.html>  
<http://tomlee.co/2013/05/traits-structs-and-impls-in-rust/>