---
title: "使用clap-rs 建構程式介面"
date: 2016-07-24
categories:
- rust
tags:
- rust
series: null
---

最近小弟在改 rust completion tool: racer 的code ，發現它用的程式介面crates: clap-rs還不錯，值得專文介紹一下：  

其實這不是第一個類似的套件，事實上已知有以下這幾個選項：  
* [getopts](https://github.com/rust-lang-nursery/getopts)  
* [docopt](https://github.com/docopt/docopt.rs)  
* [clap-rs](https://github.com/kbknapp/clap-rs)  
<!--more-->

程式介面的構造，最重要的就是：剖析使用者輸入的參數  

getopts 是在研究 rust coreutils 的時候遇到的，它的 chmod 使用getopts 來剖析參數，問題是getopts 只能功能有限的參數剖析程式，
它的參數選項有限，由 - 開頭的設定也是很大的限制，這在chmod 遇到問題，因為chmod 允許大量的選項變化：  

```bash
chmod -x file
chmod -0700 file
chmod -rwx file
```
都是可接受的  
而getopts 遇到 '-'，就把後面的內容視為參數，若不曾設定任一字母的 optflag 就會丟出 UnrecognizedOption error  
但我們也不能把 01234567rwx 都加到getopts 的flags 裡面，它們會出現在opts.usage 裡面，
[這段程式碼](https://github.com/uutils/coreutils/blob/master/src/uu/chmod/src/chmod.rs#L118-L134) 就是要排除這個問題，
在opts 處理剖析args 之前先手動剖析它，並把符合 -rwxXstugo01234567 的選項先移除掉。  

曾經把這個問題回應到 [getopts 那邊](https://github.com/rust-lang-nursery/getopts/issues/43)，
作者的建議是修改getopts 讓它在遇到 unrecognized option時，可以接到使用者定義的函式；或者讓unrecognized argument 轉為free argument。  
不過後來這些都沒有解XD，getopts 好像也有段時間沒有維護了。  

我們還是說回clap-rs好了  

clap-rs 作者自己有說了，getopts 不是不好，在簡單的小程式上getopts 足以應付大多數需求，不太需要配置記憶體也讓getopts 做到極簡，
但缺點是很多東西要自幹，像是檢查參數、自訂help 訊息等，實作額外功能時，不配置記憶體的優勢隨即消失。  
另外跟docopt 相比的話，docopt 讓你「寫help 訊息，parse 後幫你產生程式介面」，缺點是比較難客製化，parser 也比直接設定還要肥一點（雖然處理argument這通常不是什麼問題）  

來看看clap-rs 怎麼用：  

首先引入clap的 App, Arg，clap 的設計是一層層加上去，宣告App::new之後，要加什麼功能就呼叫對應函式，最後於末尾放上 get\_matches把選項爬一遍，程式介面就建完了。  
先來看看最簡單的例子，建一個空殼子claptest：  
```rust
extern crate clap;

use clap::{App, AppSettings};

fn main() {
let matches = App::new("Test program")
  .version("1.0")
  .author("yodalee")
  .about("My suck program").get_matches();
}
```
它會自動產生 help, version, usage：   
```bash
claptest --help：

Test program 1.0
yodalee
My suck program

USAGE:
    claptest

FLAGS:
    -h, --help Prints help information
    -V, --version Prints version information
```

可參考 Clap [App 的文件](http://kbknapp.github.io/clap-rs/clap/struct.App.html)

當然這樣太乾了，介面通常要加上Argument參數，大體跟app 一樣，串接一個  
```rust
.arg(Arg::with_name('name'))
```
Arg 要哪些功能一樣一一往後串接，以下介紹幾種Argument 的設定方式：  

1. 是讓程式判斷相關參數是否出現：  
```rust
.arg(Arg::with_name("debug")
  .short("d")
  .help("execute in debug mode"))
```
使用matches.is\_present()可叫出是否有這個參數。  

2. 取得參數後的值：  
設定參數takes\_value(true)  
```rust
.arg(Arg::with_name("debug")
  .long("debug")
  .short("d")
  .takes_value(true))
```
利用 matches.value\_of("debug") 取得其值，參數值可接受下列方式設定：  
```bash
-d value, --debug value
-d=value, --debug=value
-dvalue
```

3. 非參數的值，這是針對「不是hyphen」開頭的參數，不用設定long, short，可以直接抓：  
```rust
.arg(Arg::with_name("arg"))

matches.value_of("arg")
```
如果設定multiple ，可以一次抓一排：  
```rust
.arg(Arg::with_name("arg")
  .multiple(true))

let trail: Vec<&str> = matches.values_of("arg")
  .unwrap()
  .collect()
```
其他還有：  

| 用途 | 設定名稱 |
|:-|:-|
| 設定某個參數是否一定要出現 | required |
| 要不要在如有debug 參數時才出現 | required_unless |
| 是否跟其他參數有衝突 | conflicts_with |
| 參數是否要蓋掉其他參數 | overrides_with |
| 是否需要其他參數 | requires |
| 從help 訊息中將參數說明隱藏 | hidden |
| 設定參數後可能的值 | possible_values |
| 取得參數重複的次數 | number_of_values |
| 設定help 中參數更多的資訊 |  next_line_help |

作者似乎從docopt搬來一些指令，像是在Arg 可以用 [arg\_from\_usage](http://kbknapp.github.io/clap-rs/clap/struct.App.html#method.arg_from_usage) 打入argument 的使用方式來產生Arg，
個人還是不喜歡這種方式啦，感覺怪詭異的，也就不介紹了，可見[文件](http://kbknapp.github.io/clap-rs/clap/struct.Arg.html)  

在App 中使用subcommand設定子命令，就像git add 這樣： 
```rust
.subcommand(SubCommand::with_name("add"))
```
subcommand 下就跟App 設定一樣，可以用.arg 設定給subcommand 的argument  

App也有各種選項能設定subcommand 的參數跟主程式參數要如何互動，像是subcommand的alias，在help 裡
[出現的順序](http://kbknapp.github.io/clap-rs/clap/struct.Arg.html)  

雖然自己都沒有用，不過還是大致把clap-rs 的功能介紹了一遍，大概就是比getopts 還要強大的介面產生工具，功能繁多，不過能讓打造介面輕鬆許多  
當然一開始提到的，chmod 的介面在getopts 上面有問題，clap-rs 也不例外，目前這個問題無解，雖然在AppSetting 上面有選項為AllowLeadingHyphen，但開了這個選項似乎會打破一些 parse 規則，變成parse 錯誤，我已經 file bug 了，還待修正  

ps 說實話其實clap-rs 維護頻率也下降了，有沒有人要fork 一下(X