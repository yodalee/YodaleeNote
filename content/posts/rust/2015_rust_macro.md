---
title: "Rust Macro 簡介"
date: 2015-04-30
categories:
- rust
tags:
- rust
- macro
series: null
---

今天要講的是[Rust Macro](https://doc.rust-lang.org/book/macros.html):  

Rust 的Macro 是個有趣的功能，能讓你對原始碼在編譯時期進行擴展，最熟悉的例子大概是 println! 了。  
<!--more-->

故事是這樣子的，Rust 有相當嚴格的語法結構：
函數要有同樣的特徵，每個overload function 應該存在同樣的trait 中，使用同一個trait 就能為一個function在不同的物件中進行實作。  

例如在 [struct]({{< relref "2015_rust_struct_impl_trait.md">}}) 那篇中：  

我們當範例的struct Car, trait Movable，之後我們要有新的物件，只要再實作(impl) 這個trait ，就可以呼叫該function，
編譯時期會對trait 型別進行檢查，但這樣造成的問題是，對不同物件想要有同樣函數實作時，可能會有大量同樣的程式碼需要重寫。  

這裡可以取用Macro 來解決，Macro 會在編譯時展開成各種不同版本，可以一一對應到不同的型態上，當然這會讓含有Macro 的code 變得更難懂，
因為Macro 如何實作……通常會被隱藏起來，但好好使用可以讓code 變得異常的精簡，算是有好有壞的功能，只要在使用時好好注意即可。  

一般最常用到的macro ，大概像vec!，我們可以用  
```rust
let x: Vec<u32> = vec![1,2,3];
```
像 vec! 這樣的寫法可以初始化一個Vector，這就是利用Macro：  
```rust
macro_rules! vec {
    ( $( $x:expr ),* ) => {
        {
            let mut temp_vec = Vec::new();
            $(
                temp_vec.push($x);
            )*
            temp_vec
        }
    };
}
```

每個Macro 都會由 `macro_rule!` 開頭，定義哪個字詞會觸發這個Macro，之後定義展開規則，這樣vec! 都會依規則展開。  
下面會是(match) => ( expansion ) 的形式，編譯時match 會去比對Rust syntax tree，Macro 有一套自己的[文法規則](https://doc.rust-lang.org/reference.html#macros)  
規則可以像上面這樣虛擬，也可以非常明確，就是要指定某個文字內容，像這樣簡單的Macro 也是會動的：   
```rust
macro_rules! foo {
    (x) => (3);
    (y) => (4);
}
fn main() {
    println!(“{}”, foo!(x));
}
```

同時Macro 在展開時也會檢驗是否有不match 的部分，上面的 foo!(z) 會直接回報編譯錯誤；
Macro 中可以指定metavariable，以 $ 開頭，並指定它會對應什麼樣的辨識符號，
我們這裡指定match rust 的expr，並以x 代稱，外層的 $(...),* 則是類似正規表示法的規則，說明我們可以match 零個或多個內部的符號。  

在match 之後，原有的程式碼就會在{}, ()或 [] 內展開成expansion，可以在裡面recursive 的呼叫自己，但無法對變數進行運算，如下的 recursive 運算的macro rule是不行的：  
```rust
($x:expr) => RECURSIVE!($x-1)
```
在vec 中內層的 `{}` 則是要包括多個展開的expression，如果是上面的 `(x) => (3)` 就沒這個必要；展開之後，會依照指定的數量 `$(...),*` ，將內含的metavariable 展開。  
所以上面的vec![1,2,3]，就會展開成   
```rust
temp_vec.push(1);
temp_vec.push(2);
temp_vec.push(3);
```

Rust 這樣的Macro 設計是基於syntax parser 的，所以不必擔心像C macro 會遇到的問題，例如：  
```c
#define FIVE(x) 5*x  
FIVE(2+3)
```
如果是Rust 的Macro ，後面的2+3 是會直接parse 成一個expr，因此仍會正常運作，內部的$x 名稱和展開的名稱也不會有任何衝突，不用擔心C Macro字串展開後可能取用到其他變數的問題。  
```rust
macro_rule! FIVE {  
    ($x: expr) => (5*x)  
}   
```

在Rust 裡可以進行Macro matcher 的東西非常多，上面的expression 只是當例子，其實這些都可以寫到matcher 裡面，並有對應的要求，
這裡就只羅列幾個可能會用到容，詳細就請看[文件](https://doc.rust-lang.org/reference/macros-by-example.html#metavariables)了。  

| | |
|:-|:-|
| item   | 函式、struct 的宣告等等 |
| block | {} 內的內容 |
| stmt   | statement |
| expr   | expression
| ty        | 型別名稱，如 i32 |
| ident | 變數名稱或關鍵字  |

這裡有另一個 [Macro 的例子](https://github.com/neykov/armboot/blob/master/libarm/stm32f4xx.rs)：  

這是用Rust 來寫stm32 嵌入式系統，類似標頭檔的內容。  
可以看到RCC() 會回傳一個RCCType 的struct，而這個RCCType 會是RCCBase Macro 展開的結果，接著會是另一個Macro，一路展開下去就會得到一個u32的位址，指向RCC register 所在的記憶體位址。  

另外必須要說，我記得我碰過一個Macro 展開錯誤時的bug，那個錯誤真的非常非常難找，它就指向使用Macro 的那行，
送一個錯誤訊息給你，可是你根本不知道是它展開到哪裡時出了錯。  

上面這些，我的觀察啦，其實不太常用到，因為程式碼要長大到一定程度，選用Macro 才會有它的效益，一般狀況下用到的機會其實不大。  
但Rust 的確提供這樣的寫法，在必要的時候，Macro 可以用極簡短的code 達到非常可怕的功能。  