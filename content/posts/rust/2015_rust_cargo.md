---
title: "Rust Cargo"
date: 2015-05-13
categories:
- rust
tags:
- rust
- cargo
series: null
---

佈署是現代程式設計遇到的一個問題，雖然網路的出現讓大家可以快速的流通成品，同時也帶來各種版本混亂。  
這個問題在C/C++ 上不嚴重，主因C/C++的跟底層黏著度高，演化速度也慢，都是透過作業系統的套件更新。  
相對的我們可以看到無論python 的pip、Ruby的RubyGems、Golang 支援從github 取得project、NodeJS的npm，都是要建立一個統一的套件佈署管道，方便設計師開發。  

今天要提的，就是Rust 的解決方案: Cargo，用來管理rust project，當然如果不用cargo，就算像之前的嵌入式系統一樣，直接寫一個rust檔案並用Makefile + rustc 編譯也是沒有問題的。  
<!--more-->

安裝好cargo使用cargo new即可生成一個新的rust project資料；跟先前提到的一樣，Cargo new 時即會生成一個git repository和它的.gitignore，方便套件版本控制。  
project的資料會使用Cargo.toml這個檔案來管理，toml 是一款[極簡的設定格式](https://github.com/toml-lang/toml)。  

Cargo.toml 裡面會定義這個package 的資料：  
```toml
[package]  
name = "package name"  
version = "0.1.0"  
authors = ["author <author@xxxxx.com>"]   
```
Cargo 有一系列可用的指令，用cargo --help 就可以看到  
```txt
build Compile the current project  
clean Remove the target directory  
doc Build this project's and its dependencies' documentation  
new Create a new cargo project  
run Build and execute src/main.rs  
test Run the tests  
bench Run the benchmarks  
update Update dependencies listed in Cargo.lock   
```
一般最常用的組合，大概就是 new, build, run 三個基本指令，用來初始、編譯、執行，預設會用src/main.rs當作預設的編譯目標，
並建構在target資料夾內，下面是其他的功能：  

## 相依套件：

如果要用到其他的套件，把相依的套件名字填入Cargo.toml裡面，以下幾種寫法都可以，第一種是最常見的：   
```toml
[dependencies]  
package "package version"  

[dependencies.package]  
git = "url"  

[dependencies.package]  
path = "path"   
```
第二種跟第三種都是特化，不走 [crates.io](https://crates.io) 而是從 url 或是本地端取得套件，一般都是要測試最新版或修套件的時候才會用到。  
在原始碼用extern指定它即可：   
```rust
//main.rs  
extern package  
use package::{};   
```
Cargo build 的時候會自動去檢查相依性套件，從它的git repository裡面簽出最新的master版本放到家目錄的.cargo 中，並用它進行建構；
簽出的版本會寫進Cargo.lock，如果把Cargo.lock 傳給別人，他們就只之後就能用這個版本建構，如果要更新Cargo.lock 的話，
就要用cargo update 來更新相依的套件，或用cargo update -p package指定更新某套件。   

## 使用本地套件：

如果需要修相依套件裡面的bug，cargo 可以指定用本地的套件，而非簽出在.cargo 裡面的套件，只要在project 往上到根目錄的任一個地方，產生一個.cargo 的目錄，並在裡面建立config 檔，標示local project 的Cargo.toml 所在：  
```toml
paths = ['path to local project']  
```

## 測試：

cargo test 會執行在src 跟tests 裡面的測試，也就是有#[test] attribute 的，算是一個不錯小工具。  

如果拿[servo](https://github.com/servo/servo/blob/master/components/servo/Cargo.toml) 當例子：  

一開始先定義package:  
```toml
[package]  
name = "servo"  
version = "0.0.1"  
authors = ["The Servo Project Developers"]   
```
servo要編出的library  
```toml
[lib]  
name = "servo"  
path = "lib.rs"  
crate-type = ["rlib"]   
```
下面有一大排dependency，都是servo project 內的子專案，所以都是用相對路徑的方式來定義，
而這些子專案的Cargo.toml內又會定義相依套件，例如外部相依大部分定義在util 裡面，這就會用git 的方式來引用：  
```toml
[dependencies.azure]  
git = "https://github.com/servo/rust-azure"   
```
有一次有寫到一個issue 就是要更動相依的rust-mozjs的套件，再更新servo 內Cargo.lock 檔，相關的更動可見：  
<https://github.com/servo/mozjs/pull/29>  
<https://github.com/servo/servo/pull/4998>  

## 參考資料：
* [cargo](http://doc.crates.io/guide.html)
* [crates.io](https://crates.io/)