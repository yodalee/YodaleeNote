---
title: "實作麻雀雖小五臟俱全的程式語言"
date: 2018-06-16
categories:
- rust
tags:
- coursera
- pest
- parsing expression grammar
- rust
series: null
---

故事是這樣子的，很早以前曾經看過 understanding computation [這本書](http://computationbook.com/)，
這本書第二章的內容，是利用操作語義（operational semantic）的方式，自訂一款極簡程式語言，非常簡單但已經有 if 判斷式，while 迴圈等功能。  
最近剛修完 coursera 上面的 [programming language](https://zh-tw.coursera.org/learn/programming-languages)，
其中有一個作業也是用 racket 的操作語義定義一款程式語言， 這個程式語言更複雜，在資料結構上支援 pair -> list，同時還支援函式，這是之前 Understanding Computation 沒有實做的部分。  
<!--more-->

花了幾天的時間，把過去的 code 擴展了一些，在那上面實作了函式，在這裡就簡單介紹一下相關的內容，還有一些個人的心得，
心得內容可能有對有錯，如果有錯就請路過野生的大大們指教一下：  

要看到原本的內容，可以參考
* [blog 筆記]({{<relref "2016_rust_recursive_structure.md">}})
* [Github 上面的原始碼](https://github.com/yodalee/computationbook-rust/tree/master/src/the_meaning_of_programs/simple)
* 本次[修改的程式碼](https://github.com/yodalee/simplelang)

所謂操作語義，就是明白的定義程式的各指令實際執行起來是如何，實際執行的機器當然是一台虛擬機，模擬執行的過程。  
原本書裡面有兩種操作語義的方式，一種是小步 reduce，每次將程式的內容變小一些些；一種則是直接 evaluate，有什麼結果直接計算出來。  

要實作函式的部分，我把 reduce 的實作刪掉了，因為我實在不知道要怎麼用 reduce 實作函式，reduce 每次只會拿一個指令，然後把它縮小一些些，
但在處理 function 上，只要進到 function 內部就要代換成另一個環境給它，步步執行的 reduce 做不到這點。  
因為我的程式是來自於 Understanding Computation，所以裡面有些 code 像 while, sequence 是來自書中，其實我們有了 function ，
就可以用 recursive 的方式取代 while，sequence 也可以適度修改，例如把 assign 變成如 let var = val in expression 的形式，
在環境裡將一個值賦值給變數之後，以這個環境執行第二個 expression，就不需要 sequence 這樣的語法了；這部分大家自己知道就好。  

## 加法
首先我們定義我們程式的單位：Node，要實作加法需要實作兩種 Node，代表數字和代表加法運算的 Node：
```rust
pub enum Node {
    Number(i64),
    Add(Box<Node>, Box<Node>),
}
```
接著我們就可以用 Node::number(100) 代表數字，用 Node::add(Node::nubmer(3), Node::number(4)) 代表加法；
另外要實做一個 evaluate 函式，讀入一個 Node 並做出對應的操作，例如加法是分別把兩個參數都 evaluate 過，用 value 取值，
用我們熟悉的加法加起來；其他運算如乘法、判斷用的大於、小於，都是類似的實作。  
```rust
fn evaluate(&self, env: &mut Environment) -> Box<Node> {
    match *self {
        Node::Add(ref l, ref r) => {
            Node::number(l.evaluate(env).value() + r.evaluate(env).value())
        }
    }
}
```

# 變數
再深入一點要實作變數，例如 x = 10，就會需要[環境](https://github.com/yodalee/simplelang/blob/master/src/simple/environment.rs)，
它是 evaluate 需要的參數，實作是一個簡單的 HashMap，將變數名稱映射到相對應的 Node 上面。  
注意是 Node 不是實際地址，在我們的實作下輸入地址都是虛擬化為 Node；如此一來就能定義 Variable 跟 Assign 兩種 Node，分別會從環境中拿出值和將某段程式賦予給某個變數 。  

再來就是複雜一些的 Pair, List，先定義 pair 以及兩個輔助用的 fst, snd Node，一個 pair 其實就是把兩個程式組合在一起，之後可以用 fst 跟 snd 取出第一個和第二個的值。  
在這裡我們偷懶一下，重複使用 donothing 這個 Node 來表示 list 的結尾，一個 list 即是表示為許多 pair 的嵌套，最後一個 pair 的第二個 Node 必須是 donothing。  
使用 iter 搭配 fold 就能輕易將 rust 的 integer vec 轉成我們這個程式語言中的 integer list，從最後一個元素開始，一個一個用 pair 與上一次的結果組合起來。  
```rust
pub fn vec_to_list(v: Vec) -> Box {
  v.iter()
    .rev()
    .fold(Node::donothing(), |cdr, car| Node::pair(Node::number(*car), cdr))
}
```
結果：   
```txt
pair (1, pair (2, pair (3, pair (4, pair (5, do-nothing)))))
```

這裡有個小小的心得是，程式和資料其實是不可分開的，當我們在組合程式的過程，定義一些特定的組合方式就能將程式轉為資料，反之亦然；
雖然這是我偷懶的關係，但 DoNothing 可以是程式，表示不做任何事情，也可以是資料，用來表示 pair 的結尾；程式和資料其實是一體兩面，端視我們執行的時候怎麼處理它。  

我們來看一下函數，我們創了三個相關的 Node：  

* Fun：參數是一個 string 作為函數名稱，一個 string 作為變數名稱，還有一個 Node 是函式內部的程式碼。
* Closure： 我一直很好奇 closure 到底有沒有標準中文翻譯，看到有些翻譯稱為閉包，
Closure 是執行時遇到 Func 產生的東西，包含函式內的程式碼，以及 evaluate Fun 時的環境。
* Call：以給定的參數傳給一個 Closure 並執行。

把 Fun 丟進 evaluate 會把當下的環境打包起來，生成一個 Closure；如果是 Closure 的話就不會特別做什麼。  
Call 是最複雜的，它有下列幾個步驟：  

1. 把 closure 跟參數 evaluate 過，如果拿到的不是closure 就會發生錯誤。
2. 將 closure 儲存的環境跟函式取出來。
3. 在這個環境中加上兩個新的變數：一個是函數名稱指向自己這個 closure，這樣在函式內 Call 自己的名字就能做到遞迴呼叫的效果； Fun 的參數名稱指向傳進來的變數值。
4. 用新的環境去 evaluate Fun 所帶的程式。

其實如果寫過 closure ，了解相關的概念之後，再去看下面這個 [functionalC](https://github.com/cioc/functionalC) 的 repository 就滿好懂的了，
如果要實作 Functional Programming 裡面的概念，函式都要自帶一個執行的環境，才能把函式像 first class member 一樣丟來丟去，
由於 C 的函式並沒有強制要求這點，所以這一個 repository 裡面才會自己定義 closure 這個 struct ，
基本上和我的定義一樣，都包含一個真正要執行的函式，還有執行的環境。  
```c
struct closure {
  void *(*fn)(list *);
  list *env;
};
```

再深入一點，假設程式一開始先設定 1000 個變數，然後再定義一個函式，這個函式要包含的環境是否需要這 1000 個變數？
如果完整複製所有環境，太浪費空間了，實際上我們只需要記下函式中真正需要的變數即可，以下面這個函數為例子：  
```rust
let x_add_y = Node::fun(
  "add1",
  "y",
  Node::add(Node::variable("x"), Node::variable("y")));
```
它接受一個參數 y 並將它和變數 x 相加 ，這時只要記錄 x ，其他變數都不需要保存，連變數 y 也不需要，因為 y 一定會在呼叫函式的時候被參數 y 給蓋掉（Shadow）。  
變數 x 我們稱之為 free variable ，沒有被程式中的 assign 賦值或是以參數的方式掩蓋掉，它在執行時可視我們的環境設定自由變動。  

我在 evaluate.rs 另外寫了一個 cal\_free\_vars 的函式來計算一段程式內的自由變數，它會生成兩個 HashSet 記錄出現過的變數跟自由變數，然後丟給 helper 函式處理。  
大部分的處理方式都差不多，就是一路遞迴往下呼叫，像加法就是分別對兩個 Node 計算內部的自由變數；比較不一樣的是 Variable, Assign, Fun；在 Assign 跟 Fun 的地方，分別要把變數名稱、函數名稱跟參數名稱加到變數名單中，如果 Variable 取用的變數還沒在變數名單內，這個變數就是自由變數。  
最後修改 evaluate Call 的地方：  
```rust
Node::Call(ref closure, ref arg) => {
    let arg = arg.evaluate(env);
    let clsr = closure.evaluate(env);
    match *clsr {
        Node::Closure(ref env, ref fun) => {
            if let Node::Fun(funname, argname, body) = *fun.clone() {
                let freevars = get_free_vars(&fun);
                let mut newenv = Environment::new();
                for var in freevars {
                    newenv.add(&var, env.get(&var));
                }
                newenv.add(&funname, clsr.clone());
                if !argname.is_empty() {
                    newenv.add(&argname, arg.clone());
                }
                body.evaluate(&mut newenv)
                } else {
                    panic!("Closure not contain function: {}", fun)
                }
```
用 get\_free\_vars 得到函式內的自由變數，生成一個新的環境，從現在的環境取得自由變數的值，用新的環境產生 closure；
如果環境中沒有自由變數的值，環境的實作會直接崩潰，強制在執行函式的時候，環境中必須要有它的記錄。  

以上大概就是一個有函式的程式語言會需要的實作，基本上這個語言能做到一些相當複雜的事，例如遞迴跟 currying 等，在 evaluate.rs 裡有一些相關的測試，例如階乘的遞迴實作：  
```rust
fn test_simple_big_function_recursive() {
    let factor = Node::fun("factor", "x", Node::if_cond_else(
            Node::gt(Node::variable("x"), Node::number(1)),
            Node::multiply(Node::variable("x"),
              Node::call(Node::variable("factor"), 
              Node::subtract(Node::variable("x"), Node::number(1)))),
            Node::number(1)));
    let statement = Node::sequence(
        Node::assign("entry", factor),
        Node::assign("result", Node::call(Node::variable("entry"), Node::number(10)))
    );
    let mut env = Environment::new();
    println!("{}", statement.evaluate(&mut env));
    assert_eq!(3628800, env.get("result").value());
}
```
寫完這款程式語言，我開始覺得其實我是在寫個虛擬機，或者說有點像在實作一台電腦。  
我們先把所有的資料：數值、真假值虛擬化為 Node 這個單位，一切的操作都是在 Node 上進行；就像真實的 CPU，也是將數字轉化為記憶體內部的 0, 1，在加法這個指令被執行的時候，會拿出記憶體的內容，通過一連串的邏輯閘變成輸出，再存回記憶體。  
記憶體就好比我們的 Node，邏輯閘實作則是 evaluate，CPU 執行 x86 指令這款「語言」對應我們自訂的程式語言，只是CPU是真實的機器，我的程式是一台虛擬機 。  
程式其實根基於數學，加法是一個概念，我們只是透過 CPU/電腦的實作，亦或是這篇文的操作語義，用虛擬機模擬出加法這個概念，所謂「程式語言」應是數學之神座下超凡的存在。 我們用上人類智慧的極致，打造 CPU，打造電腦，試著去追趕的這神聖的目標，追之求之，卻稱這款模倣的玩意兒為「程式語言」，何等自傲？想想不禁啞然失笑。  