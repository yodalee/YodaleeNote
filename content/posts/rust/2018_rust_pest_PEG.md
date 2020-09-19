---
title: "使用 rust pest 實作簡單的 PEG simple 剖析器"
date: 2018-05-06
categories:
- rust
- parsing expression grammar
tags:
- rust
- pest
- parsing expression grammar
series: null
---

[上一篇]({{< relref "2018_PEG.md">}})我們看了 PEG 相關的內容，這篇我們就來介紹該如何用 PEG 寫一個簡單的剖析器。  
<!--more-->

當初會開始這系列文章，是因為自己 computation book rust 實作中，並沒有像[原作者的 ruby 實作](https://github.com/tomstuart/computationbook)，
有用 [treetop](https://github.com/nathansobo/treetop) 這個 PEG parser 寫一個剖析器，剖析文法變成裡面的程式，
例如 simple, regupar expression, pushdown automata, lambda calculus 等等，最近想說把這部分補上，結果在第一關 simple 上就研究了好一陣子。  
本來預估一個星期寫完，根本太樂觀，回家晚上能自己寫 code 的時間估太多，到現在應該已經快一個多月了，才有初步的結果，
當然我們也可以說原因是 rust pest 沒有 ruby treetop 這麼好用（炸。  

要使用 rust pest，首先是透過 cargo 安裝，為了這點我一開始先花好一陣子，把整個 project改寫成 cargo 管理，
詳見[這篇文章]({{< relref "2018_rust_module.md" >}})，
之後才開始相關的實作，整個完成的程式碼可以看[這裡](https://github.com/yodalee/computationbook-rust/tree/master/src/the_meaning_of_programs)：  

安裝 pest，在 Cargo.toml 中加上：  
```toml
[dependencies]  
pest = "^1.0"  
pest\_derive = "^1.0"
```
pest\_derive 為 pest 剖析器產生器，他會分析你指定的 PEG 文法，生成對應的剖析規則跟剖析器；pest 則是引入剖析後生成的資料結構，兩個都要引入。  
在原始碼中加入：  
```rust
#[cfg(debug_assertions)]  
const _GRAMMAR: &'static str = include\_str!("simple.pest");  
#[derive(Parser)]  
#[grammar = "the_meaning_of_programs/simple.pest"]  
struct SimlpeParser;
```
\_GRAMMAR 是用來提醒編譯器，在 simple.pest 檔案更新的時候，也要觸發重新編譯（不然就會發現改了文法，cargo build 不會重新編譯），
該 pest 檔的路徑是相關於目前的原始碼檔案；grammar 後的路徑則是相對於 src 資料夾，我試過不能用 .. 的方式回到 src 上一層目錄，
grammar 檔案內容就是PEG 的語法，在編譯的時候會被 pest 轉換成 parser 的實作儲存在 SimpleParser 裡面。  

pest 的語法基本上跟 PEG 沒有太大差別，在文法檔案中，就是 rule = { rule content } 的方式去定義規則：  

* 匹配字串使用雙引號包住，用 ^ 設定 ASCII 為無關大小寫，例：op\_add = { "+" }, const = { ^"const" }
* 一定文字範圍的用單引號搭配 ..，例：number = { '0’..’9’ }
* 選擇規則用 | ，例：alpha = { 'a’..’z’ | 'A’..’Z’ }
* 連結規則用 ~，跟 PEG 定義用空白直接連接不同，空白在 pest 用做排版，例：stat_assign = { variable ~ "=" ~ expr ~ ";" }

定義規則中，可以用到其他規則，例：factor = { (variable | number) }。  
另外有一些特別的規則，包括：  

* whitespace：whitespace 裡指定的字串，會自動在 ~ 連結的位置中插入 (whitespace)*，
平常不需要特別指明處理 whitespace，例如上面的 stat\_assign 就變得能夠剖析 "foo = 123" 而不只是 "foo=123"。
* comment：comment 會在規則和子規則間被執行，不需特別指明。
* any：匹配任一字元，對應 PEG 中的 .。
* soi, eoi：對應匹配內容的開始和結束，這兩個還滿重要的，以之前的 S = A, A = aAa | a 為例，
如果直接寫 S = { A }，那去匹配一個以上的 a 都會匹配成功，因為我們沒指定 S 之後要把整個字串匹配完，正確的寫法是：S = { A ~ eoi }。
* push, pop, peek：分別 push/pop/peek 字串到 stack 上面，push(rule) 將 rule 匹配到的字串送到 stack 上；
epop/peek 會用 stack 內容的字串去做匹配，但 pop 會消耗掉 stack 的內容；這個規則我還沒有實際用過，不確定哪裡會用到它。

---

由於 pest 的文法規則都會被轉成一個 rust enum ，所以 rule 的取名必須避開 rust 的關鍵字，我在這裡是加上一些前綴或後綴來迴避，例如 stat\_while；規則在剖析過後會生成對應的 token，內含剖析到的字串，如果是直接實寫的文字就不會產生出結果，這部分等等會看到。  

* 用 // 在規則中寫註解。
* PEG 中 ?+* 三個符號，也是直接加上，有需要特別分隔的地方，可用小括號分開，例：
```txt
number = @ { (digit)+ }、stats = { (stat)* }
```
* e{n}，e{,n}，e{m,}，e{m,n}：分別是 n 個，至多 n 個，m個以上，m至n個匹配。
* PEG 的 & 跟 ! predicate 也是直接使用（不過我沒用過XD）

每個規則前面可以加上四個 optional modifier，分別如下：  

* Silent \_ ：剖析的時候不產生這個規則對應的節點，例如我的 factor 是：
```txt
factor = _{ (variable | number) }
```
那在剖析完之後，會直接跳過 factor，產生 variable 或 number 的節點。
* Atomic @：這跟上面的 whitespace 有關，像我的 variable 寫成 `variable = { (alpha) ~ (alpha | digit)* }` ，豈不是可以接受 "a 123" 這樣奇怪的變數名？這時候就用 @ 確保規則中不執行 whitespace 規則。
* Compound-atomic $：這跟 atomic 一樣，只是規則的子規則，例如 `expr = $ { "-" ~ term }` ，則 term 仍然適用 whitespace。
* Non-atomic !：因為一個 atomic 規則下所有規則都會是 atomic，可以用 ! 來停止這樣的效果。

我們可以把上面這些都綜合起來，寫出一個極簡的 simple language parser，當然這實在是太簡單了，簡單到會出一些問題：  

```txt
alpha = { 'a'..'z' | 'A'..'Z' }
digit = { '0'..'9' }

whitespace = _{ " " | "\n" }

variable = @ { (alpha) ~ (alpha | digit)* }
number = @ { (digit)+ }

op_add = { "+" }
op_mul = { "*" }
op_lt  = { "<" }
op_binary = _ {op_add | op_mul | op_lt }

factor = _{ (variable | number) }
expr = { factor ~ (op_binary ~ factor)* }

stat_assign = { variable ~ "=" ~ expr ~ ";" }
stat_while = { "while" ~ "(" ~ expr ~ ")" ~ "{" ~ stats ~ "}" }
stat_if = { ("if" ~ "(" ~ expr ~ ")" ~ "{" ~ stats ~ "}" ~ "else" ~ "{" ~ stats ~ "}" ) |
            ("if" ~ "(" ~ expr ~ ")" ~ "{" ~ stats ~ "}") }
stat = _{ ( stat_if | stat_while | stat_assign ) }
stats = { (stat)* }

simple = _{ soi ~ stats ~ eoi }
```

simple 就是整個剖析的進入點，在原始碼中呼叫 SimpleParser 的 parse 函式，對字串進行剖析，參數要代入想要剖析的規則和內容，
這裡我們用 expression 來舉例，畢竟寫過 parser 就知道 expression 算是最難爬的東西之一，通常搞定 expression 其他都是小菜一碟：  
```rust
let pair = SimpleParser::parse(Rule::expr, "1 * 2 + 3 * 4")
                .unwrap_or_else(|e| panic!("{}", e))
                .next().unwrap();
```

parse 之後會得到一個 `Result<Pairs<R>, Error<R>>`，表示是否成功，這裡如果不成功我們就直接 panic ，成功的話取出 Pairs，
用 next unwrap 將第一個 Pair 取出來，也就是剖析完的 Expr Token，因為剖析失敗的話在剛剛的 Result 就會得到 Err 了，這裡我們都可以大膽的用 unwrap 取出結果。  

Pair 有幾個函式可呼叫：  

* pair.as\_rule() 會得到剖析的規則，此時的 pair.as\_rule() 為 Rule::expr，這可以用來判斷剖析到什麼東西。
* pair.into\_span() 會取得 token 的範圍資訊。
* pair.into\_span().as\_str() 會得到 token 匹配的字串內容，像在處理 assign的時候會用這個拿到變數名稱 。
* pair.into\_inner() 會拿到下一層的 Pairs，
以 expr 來說，會對應到 `{ factor ~ (op\_binary ~ factor)* }`，之前有提過字串並不會產生 token，上面的 stat\_if, stat\_while 就是例子，在 into\_inner 的時候，括號、角括號等只是匹配，但不會有 token 產生。

在這裡我們把 expr 的 Pair 直接丟下去給另一個函式 build\_expr，由它把 expression 剖析成 simple language 的 Node，它會先用 into\_inner 叫出 expr 的內容物，然後依序取出左值、運算符跟右值並建成 Node Tree；可以從 op 的處理方式看到如何使用 as\_rule() 來看看剖析到什麼。  
```rust
fn build_expr(pair: Pair<Rule>) -> Box<Node> {
    let mut inner = pair.into_inner();
    let mut lhs = build_factor(inner.next().unwrap());
    loop {
        let op = inner.next();
        match op {
            Some(op) => {
                let rhs = build_factor(inner.next().unwrap());
                lhs = match op.as_rule() {
                    Rule::op_add => Node::add(lhs, rhs),
                    Rule::op_mul => Node::multiply(lhs, rhs),
                    Rule::op_lt  => Node::lessthan(lhs, rhs),
                    _ => unreachable!(),
                }
            },
            None => break,
        }
    }
    lhs
}
```

因為我們沒有處理運算符優先順序的問題，所以 1 * 2 + 3 * 4 的結果會是 20，如果要正確處理就需要實作 precedence climbing 之類的方法，
不過這個留待[下篇文章]({{< relref "2018_rust_precedence_climbing.md">}})再來解決這個問題，
至少我們已經能 parse 一個 simple program，自動轉成 Rust 的 simple AST 了（其實原作者的 treetop parser 也沒有考慮這個問題，所以其實我們可以裝傻當作沒這回事XD）。  

以上大概就是 pest 的介紹，基本上使用 pest，一個規則用一個單獨的函式來處理，就能把每次修改的範圍縮到最小，熟練的話應該能在短時間內魯出一個基本的 parser 來用。