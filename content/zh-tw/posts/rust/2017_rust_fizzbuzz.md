---
title: "使用rust closure實作fizzbuzz"
date: 2017-08-25
categories:
- rust
tags:
- rust
- understanding computation
series: null
---

之前用Rust 重寫Understanding Computation 裡面的ruby code，目前從 github 上來看，我的 Rust code 應該是僅次於原作者的 code，完成度最高的一個版本。  
從去年五月，把大部分的 code 完成以來，唯一一個沒寫的章節：chapter 6 的 fizzbuzz，最近終於實作出來了\weee/。  
<!--more-->

本來我是用了比較直接的方法，也就是把closure 用function 來實作，使用generic 的方式來處理參數，
例如在數字的部分，我們就要接受一個函式跟一個參數，這個函式要吃一個參數然後吐一個參數……。  
例如我那時候實作的正整數的部分：  
```rust
fn ZERO<F, T>(p: F, x: T) -> T where F: Fn(T) -> T { x }
fn ONE<F, T>(p: F, x: T) -> T where F: Fn(T) -> T { p(x) }
fn TWO<F, T>(p: F, x: T) -> T where F: Fn(T) -> T { p(p(x)) }
fn THREE<F, T>(p: F, x: T) -> T where F: Fn(T) -> T { p(p(p(x))) }
fn FIVE<F, T>(p: F, x: T) -> T where F: Fn(T) -> T { p(p(p(p(p(x))))) }
```

這個寫法的問題是啥？問題在於…我必須手動處理所有的型別，這在只有數字、布林的時候還容易處理，等到型別一複雜，這種函式宣告根本寫不出來，然後編譯器噴你一臉錯誤。  
最終完成的也只有number 跟 boolean，甚至連下一段的 is\_zero 都實作不出來，程式碼我保留在 
[ch6-fizzbuzz](https://github.com/yodalee/computationbook-rust/tree/ch6-fizzbuzz/programming_with_nothing/fizzbuzz) 的分枝裡。  

最近有天心血來潮，把我的 Rust code 實作成果貼到 [rust forum](https://users.rust-lang.org/t/computation-book-example-code-implemented-in-rust/12403)。  

在討論串的下面有一位 jonh 回了我，他的辦法挺聰明的，實作的方式也比較符合這個 project 的要求，首先呢，我們不要處理這麼多型別的問題，把所有的型別都收到一個enum 之下：  
```rust
pub enum Pol {
    C(Rc<Fn(Rp) -> Rp>),
    I(i32),
    B(bool),
}
pub type Rp = Rc<Pol>;
macro_rules! r {
    ($cl:expr) => {Rc::new(Pol::C(Rc::new($cl)))}
}

impl Pol {
    pub fn call(&self, x: Rp) -> Rp {
        match self {
            &Pol::C(ref c) => c(x),
            _ => panic!(),
        }
    }
}
```

型別 Rp 是用 rust 的 reference count pointer (Rc) 包裝這個 Pol 的型別，Pol::C 則是包裝一個 Rc 包裝的函式，該函式會吃一個Rp，吐一個Rp，等於是封裝了一個 lambda 函式。  
另外我們利用自定義的 macro，讓產生這類封裝的 lambda 函式更容易，最後我們定義呼叫的 call 函式，它會把 Pol::C 裡的函式取出來，用 c 取用參數 x 執行。  
這樣，就完成了函數的基本型態。  

接著我們就能跟著這本書，一步步打造 fizzbuzz 的程式碼，例如上面提到的正整數的部分：  
```rust
let zero  = r!(|_p| r!(|x| x));
let one   = r!(|p: Rp| r!(move |x| p.call(x)));
let two   = r!(|p: Rp| r!(move |x| p.call(p.call(x))));
let three = r!(|p: Rp| r!(move |x| p.call(p.call(p.call(x)))));
let five  = r!(|p: Rp| r!(move |x| p.call(p.call(p.call(p.call(p.call(x)))))));
```

這樣寫的問題是，我必須把所有的 closure 定義寫在 main 函式裡，因為 rust 不允許以 use 的方式，引入定義在別的檔案的 closure，以致最後 main.rs 高達 600 多行。  
第二個問題是由於Rust 的所有權特性，在定義每個 closure 的時候，會需要不斷的 clone，例如 multiply 的 closure，需要用到 add 還有 zero，所以我們就要一路把 add 跟 zero clone 下去。  
寫到複雜一點的closure 例如 divide，需要使用 if, is\_less\_than, increment, subtract, zero，一個closure 的定義橫跨40 行，這寫法我覺得真的不行，不過一時之間真的找不到更好的寫法。  
```rust
// multiply
// |m| { |n| { n(add(m))(zero) } }
let multiply = {
    let add = add.clone();
    let zero = zero.clone();
    r!(move |m: Rp| {
        let add = add.clone();
        let zero = zero.clone();
        r!(move |n: Rp| {
            n.call(add.call(m.clone())).call(zero.clone())
    })
})
};
```
最後，我沒辦法把 Rp 這個函式印出來，像書裡面印出橫跨數頁，壯觀的lambda函式，這個問題也暫時無解。  

最後的成果，完成的 fizzbuzz 所下所示：  
```rust
let solution = {
  map.call(range.call(one.clone()).call(hundred.clone()))
   .call(r!(move |n:Rp| {
     _if.call(is_zero.call(module.call(n.clone()).call(fifteen.clone())))
        .call(fizzbuzz.clone())
        .call(
          _if.call(is_zero.call(module.call(n.clone()).call(three.clone())))
             .call(fizz.clone())
             .call(
               _if.call(is_zero.call(module.call(n.clone()).call(five.clone())))
                  .call(buzz.clone())
                  .call(to_digits.call(n.clone()))
             )
        )
   }))
};
```

執行起來慢的要死，fizzbuzz 1-100 費時 51s ，如果真的用 rust 寫，根本不用1 ms 好不好。  
當然了，最終能用 rust 把這篇奇文給實作出來，還是覺得滿有趣的，中途也曾出現過，因為[一個括號括錯地方](https://github.com/yodalee/computationbook-rust/commit/e63bf9cefe1cd9e41d570d7cac40fba4e0659353)，
瞬間讓 multiply 變成 power 3*5 = 243，WTF！我至今還參不透，究竟為什麼括號括錯就會讓 multiply 瞬間升一級變 power OAO  

我的程式碼都收到master branch 下面，可以參考 
[github連結](https://github.com/yodalee/computationbook-rust/tree/master/src/programming_with_nothing)，體會一下 functional programming 的奧妙之處XD  
這篇文其實根本是**重新發明輪子的極致**，不止是演算法，我們要把整個整數系統、真偽值什麼的，都重新打造一遍，
有一種我們先來種顆樹，長出來之後砍下來變木材，作成工具台之後開始打造輪子，感情我不是在寫 fizzbuzz，而是在玩 minecraft 呀(X。  