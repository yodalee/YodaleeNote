---
title: "Rust 裡面那些 String 們"
date: 2019-09-04
categories:
- rust
tags:
- rust
series: null
---

故事是這樣子的，最近把小弟自幹的編譯器加上 rust 的 llvm wrapper llvm-sys，經過一陣猛烈的攪動之後，自幹的編譯器終於可以 dump LLVM IR 了，雖然只會輸出一個空殼子…但有第一步總是好的。  
不過小弟在綁定的時候遇到一個大問題，也就是 Rust 裡面的 String，到底怎麼會有這麼多種，因為寫的時候一直沒搞清楚，然後就會被編譯器噴上一臉的錯誤，覺得痛苦，於是決定來打篇整理文。  
<!--more-->
簡單來說，Rust 的 std 有四種 String，每個 String 都有動態記憶體模式跟沒有 size 資訊（不是 Sized）的靜態模式，他們是：  

| dynamic type | static type |
| :- | :- |
| std::string::String   | std::str |
| std::ffi:OsString       | std::ffi::OsStr |
| std::path::PathBuf | std::path::Path |
| std::ffi::CString        | std::ffi::CStr | 

還有一個比較少用，只能表示 ascii 128 字元組成的字串的 std::ascii::asciiExt，在 1.26.0 已經 deprecated 了，這裡就不介紹了。  

一般的程式語言在數字型態通常都很固定，Rust 就很明確的分為 i8, i16, i32, i64 …，就偏偏字串是個大坑，
因為從 ASCII 到 unicode，字串實在有太多分岐，儘管有 unicode 也不是到處適用。
Rust 從設計上一開始就直接採用 utf-8 作為設計標準，原生的 String/str 就是 utf 8 字串。  

可是呢，並不是所有作業系統都玩 utf8 這套，因此 Rust 有另一個使用 wtf8 的 OsString，
wtf8 跟 utf8 的差異在於 wtf8 算是<格式比較差>的 utf8，會出現一些 utf8 不允許的位元組，偏偏規格沒有要求一定要完美格式，
造成 windows 或 javascript 有時會出現這種格式不良的 wtf8 字串，因此 OsString ，跟專門用來表示路徑的 PathBuf 就是使用 wtf8。  

有關 wtf8 請參考：<https://simonsapin.github.io/wtf-8/>  

上面的字串都是在型態中記錄字串長度，結尾不會有 \0 字元，CString 則是最傳統的 null-terminated 字串，在呼叫 C 函式的時候，一定要用 CString 傳遞才行。  
順帶一提，一般寫在 code 裡面的 `let hello = "hello world"` 的型態是 `&'static str`：生命週期為 static 的靜態字串。  

知道了以上幾個區別之後，就來看看要怎麼使用它們：  

## String

String 最簡單，裡面一定要是 utf8，產生就是從 static str 產生，或者是 new 之後慢慢 push 進去：  
```rust
let hello : String = String::from("hello");
let mut world : String = String::new();
world.push_str("world");
world.push('!');
```

## OsString

OsString 是類似的，但只能從 String 轉過來（注意 String 的所有權會轉給 OsString），或者一樣 new 之後 push String 進去：  
```rust
use std::ffi::{OsString, OsStr};
let oshello : OsString = OsString::from(hello);
let mut world : OsString = OsString::new();
world.push("world!");
```

## PathBuf

PathBuf 其實就想成 OsString 就好，兩者也可以互相用 from 轉換：  
```rust
use std::path::{PathBuf, Path};
let p1 : PathBuf = PathBuf::from(oshello)
let mut p2 = PathBuf::new();
p2.push("/dev");
```
上面說了，OsString 跟 PathBuf 用的是 wtf8，是 utf8 的超集，因此一般只能單向從 String 到 OsString，反向是不行的，
呼叫 `OsString::into_string()` 得到的是 `Result<String, OsString>`，也就是有可能會轉失敗；
或者就是用 `into_lossy_string` 把編碼不完整的地方變成 U+FFFD，utf8 的 replacement character。  
PathBuf 則是沒有 `into_string` 可以用，只能先轉換成 OsString 再轉過去，我也不知道為什麼 core team 要這樣設計。  

剩下的就是函式了，很有趣的是 String, OsString, PathBuf 都是動態容器，操作內容都要轉換到 str, OsStr, Path 上面去：  
* str 有操作字串用的 `split_whitespace`, `starts_with` 等等  
* OsStr 沒有任何特殊的函式XD。  
* Path 有很多對路徑的操作：`is_absolute`, `parent`, `with_extension` 等等

很多函式操作後都會得到 Path 或是 OsStr 讓你做接下來的操作。  

## CString

CString 比較棘手一點，它要在 new 的時候代入 `Vec<u8>` （或者有實作 `Into<Vec<u8>>` 的型態）
來建立 CString，new 會自動在後面加上 \0 ，因此這個 Vec 裡面不應該有 \0。  
其實我覺得把 CString 想得 `Vec<u8>` 的另一種型態就好了，它本身也提供 `into_bytes`, `as_bytes` 等函式轉換成 `Vec<u8>` 的型態。  
如果要從 String 跟 OsString 轉換過來的話，String 要用 `as_bytes()` 轉成 `Vec<u8>`，
OsString 因為 unix 跟 windows 會有不同的 OsString 實作，不一定都能轉成 `Vec<u8>`，
在 unix 要引入 `std::os::unix::ffi::OsStrExt` 就可以將 OsString 用 `as_bytes()` 轉成 `Vec<u8>`；Windows 則建議轉成 String 再轉成 bytes ，請參考這個[網址](https://stackoverflow.com/questions/38948669/whats-the-most-direct-way-to-convert-a-path-to-a-c-char)。  

用上了 CString，最重要的就是要交給外部的 C 函式去用，要用 as\_ptr() 取出字串部分的 pointer，得到的就是 * u8 了，有必要的話再加上 as *const i8 轉型一下。  
例如我要呼叫這個函式：  
[LLVMPrintModuleToFile](https://llvm.org/doxygen/group__LLVMCCoreModule.html) 
```c
LLVMPrintModuleToFile(LLVMModuleRef M, const char *Filename, char **ErrorMessage)
```

我的檔案名稱是一個 OsString：  
```rust
use std::ffi::{CString, CStr};
use std::os::unix::ffi::OsStrExt;
llvm::core::LLVMPrintModuleToFile(
    self.module,
    path.as_bytes().as_ptr() as *const i8,
    ptr::null_mut()
);
```

看了這麼多，簡單整理一下大概是這樣：  
![rust_string](/images/posts/rust_string.png)

老實說每次只要在 Rust 裡面弄到 Path 都會弄到懷疑人生……