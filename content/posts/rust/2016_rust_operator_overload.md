---
title: "Rust 中實作型別運算子重載"
date: 2016-03-30
categories:
- rust
tags:
- rust
- understanding computation
series: null
---

最近在實作computation books第九章，用到很多Rust運算子重載的部分。  
運算子重載嘛，可以對自己定義的struct 或是enum 使用運算子，這樣就能寫出 Vec3 + Vec3 這樣比較漂亮的寫法，不用 Vec3.add(Vec3)，
<!--more-->
啊雖然兩個本質上沒什麼兩樣啦  

這章定義一個Sign的類別，分為
* 正
* 負
* 零
* 未知

我們要實作他的乘法和加法：  
```rust
enum Sign { POSITIVE, NEGATIVE, ZERO, UNKNOWN, }
```
Rust可重載的運算子請參考 [ops 的文件](https://doc.rust-lang.org/std/ops/index.html)。  
另外是比較運算子 [cmp](https://doc.rust-lang.org/std/cmp)，包括 PartialEq 跟 PartialOrd：  

例如我們要重載乘法運算子，以下是網站上的定義：  
```rust
pub trait Mul<RHS = Self> {
    type Output;
    fn mul(self, rhs: RHS) -> Self::Output;
}
```
實作時當然就是先以use這個trait，然後實作這trait並加入相關的函式：
```rust
use std::ops::Mul;
impl Mul for Sign {
    type Output = Sign;
    fn mul(self, rhs: Self) -> Self {
        if self == Sign::ZERO || rhs == Sign::ZERO {
            Sign::ZERO
        } else if self == Sign::UNKNOWN || rhs == Sign::UNKNOWN {
            Sign::UNKNOWN
        } else if self == rhs {
            Sign::POSITIVE
        } else {
            Sign::NEGATIVE
        }
    }
}
```
這樣就完成了，現在我們就能這樣寫了：  
```rust
assert_eq!(Sign::NEGATIVE, Sign::POSITIVE * Sign::NEGATIVE);
```

另外常遇到的問題是，將運算子重載和Rust 的泛型一起用時，例如，我們定義 `sum_of_square` 這個 function，並希望使用泛型：  
```rust
fn inner_product<T: Copy>(lhs: T, rhs: T) -> T {
    lhs*lhs + rhs*rhs
}
```
這樣編譯並不會過，因為泛型 T 並不適用乘法跟加法，我們需要告訴編譯器，只有實作Mul跟Add trait的型別才能通過。
同時指定 Output 型別同樣為T，文件上並沒有講如何實作這部分，我忘記是在哪找到要這樣寫的，就為了那個Output=T花了我超多時間RRRRR，反正Rust 的文件就是這樣…  
```rust
fn inner_product<T: Mul<T, Output=T>+Add<T, Output=T>+Copy> -> T {
    lhs*lhs + rhs*rhs
}
```
如果你要不同的實作，例如我要能夠跟 i32 相加，那就是：  
```rust
fn foo<T: Add<i32, Output=T>>(x: T) -> T {
    x+1
}
```
個人覺得：相較之下，C++運算子重載的語法真的相當的複雜（事實上我覺得我已經不會寫了Orz），rust 簡潔不少，使用trait 中的function name來實作也比C++ 用 operator+, operator* 好讀很多。  

有關於文中所提 Sign 的實作，請參考 [Github](https://github.com/yodalee/computationbook-rust/tree/master/src/programming_in_toyland/signs)  