---
title: "Rust std process 生成子行程"
date: 2020-03-01
categories:
- rust
tags:
- rust
series: null
---

最近在玩 Rust 的時候，需要用 Rust 去呼叫一些 shell command 來幫我完成一些事，幸好 Rust std 裡面已經有 [process](https://doc.rust-lang.org/std/process/index.html)
 來幫我們完成這件事，使用起來很像 python 的 subprocess，不過實際在用遇到一些問題，所以寫個筆記記錄一下：  
 <!--more-->

首先當然是從 std 引入這個模組的 [Command](https://doc.rust-lang.org/std/process/struct.Command.html)，Stdio 很常用也順便 include 一下：  
```rust
use std::process::{Command, Stdio};
```
一切的基礎就是一行：  
```rust
Command::new(command_name)
```
在 command\_name 的地方填入你想呼叫的指令。  

Command 代表了一個準備好要跑的命令，就像是在 shell 裡面打下 command\_name 直接按 enter 一樣，沒有參數、繼續現在行程的環境、位置和現在行程的位置相同。  
如果要設定給命令的參數，就用 .arg 塞進去，如下面的例子：  
```rust
let mut ls = Command::new(ls).arg("-al");
```
這個參數一次只能塞一個，有多個參數要連續呼叫 .arg 才行。  

有個 Command 之後接下來有三種方式讓它跑起來：.spawn(), .output(), .status()：  

* spawn fork 子行程執行，拿到一個子行程的 handler，回傳的型別是 `Result<Child>`。
* output fork 子行程執行，等待（wait）它結束之後，收集它寫到 std output 的內容，回傳的型別是 `Result<Output>`。
* status fork 子行程執行，等待它結束之後，收集它回傳的資訊，回傳的型別是 `Result<ExitStatus>`。

第一個可以注意到的是回傳的型別都是 Result，這是因為 command 可能會跑起來也可能會跑不起來，像是我打一個 Command::new("www")
但我的 shell 根本沒 www 這個指令，Result 提醒了這個可能性的存在，一般來說這邊最簡單的就是用 .expect 把 Result 解開。  

第二個另人疑惑的，是後面的 Child, Output, ExitStatus 是什麼鬼，整理之下大概是這樣：  

* [ExitStatus](https://doc.rust-lang.org/std/process/struct.ExitStatus.html) 是最簡單的，
就是行程結束的狀態的封裝，Rust 提供兩個介面 success 跟 code 來判斷子行程有沒有正常結束以及對應的 exit code。
* [Output](https://doc.rust-lang.org/std/process/struct.Output.html) 是更上一層，
裡面包了一層 status : ExitStatus，加上兩個 stdout, stderr 的 Vec<u8>，裡面存了子行程所有寫到 stdout 跟 stderr 的內容。
* 最外層就是由  spawn 產生的 [Child](https://doc.rust-lang.org/std/process/struct.Child.html)，
比起 output 跟 status 一生成行程就自動幫你 wait，spawn 給了完全的操作能力，可以做更多事情。

三個啟動的函式影響最大的就是子行程的 stdin/stdout/stderr

|              | stdin      | stdout     | stderr     |
|--------------|------------|------------|------------|
| spawn/status | 繼承父行程 | 繼承父行程 | 繼承父行程 |
| output       | 不可使用   | piped      | piped      |

如果不想用預設的設定，可以在呼叫 status/output/spawn 前做設定，有三個選項可選

1. Stdio::inherit: 繼承父行程
2. Stdio::piped: 接 piped
3. Stdio::null: 接上 /dev/null 

現在就能來玩一些例子，例如在 rust 裡面呼叫 ls，用 status() 的話輸出會直接輸出到螢幕上面：  
```rust
let p = Command::new("ls")
    .arg("-al")
    .status()
    .expect("ls command failed to start");
```
```bash
drwxr-xr-x 5 yodalee yodalee 4096 2月 29 09:45 .  
drwxr-xr-x 16 yodalee yodalee 4096 2月 28 20:10 ..  
-rw-r--r-- 1 yodalee yodalee 62279 2月 29 00:07 Cargo.lock  
-rw-r--r-- 1 yodalee yodalee 312 2月 29 00:07 Cargo.toml    
```
如果想要把 ls 的內容截下來的話，就要改用 output：  
```rust
let p = Command::new("ls")
  .arg("-al")
  .output()
  .expect("ls command failed to start");
let s = from\_utf8\_lossy(&p.stdout);
println!("{}", s);
```
可以從 p.stdout 裡面拿到 Vec<u8>，要轉成字串就要用 [String](https://doc.rust-lang.org/std/string/struct.String.html)
的 `from_utf8`/`from_utf8_lossy`/`from_utf8_unchecked` 函式轉。  
```txt
drwxr-xr-x 5 yodalee yodalee 4096 2月 29 09:45 .  
drwxr-xr-x 16 yodalee yodalee 4096 2月 28 20:10 ..  
-rw-r--r-- 1 yodalee yodalee 62279 2月 29 00:07 Cargo.lock  
-rw-r--r-- 1 yodalee yodalee 312 2月 29 00:07 Cargo.toml   
```

如果要對子行程上下其手有完全的操控，就要使用 spawn 了，不過相對來說也要小心，因為 spawn 不會自動幫你 wait，不小心就會把子行程變殭屍行程。  
產生出來的 Child 物件，本身就自帶一些函式，像  

* kill() 發 SIGKILL 把子行程砍了。
* wait()、wait\_output() 等待子行程結束，spawn + wait/wait\_with\_output 就相當於直接呼叫 status/output。

我們用 shell 的 rev 當作例子，它會輸入 stdin 反轉之後輸出，這裡不能用 output() 因為 output 的 stdin 不會打開；
可以用 status ，這樣 stdin 會繼承本來的 shell 的 stdin 讓我們打字，但如果我們是要反轉程式裡面的一行字串呢？
這時候我們就要用 ~~s.chars().rev().collect::<String>() 然後這篇文就不用寫了~~ spawn 再操作 stdin 了。  

具體來說大概像是這樣：  
```rust
let mut p = Command::new("rev")
    .stdin(Stdio::piped())
    .spawn()
    .expect("rev command failed to start");
let stdin = p.stdin.as_mut().expect("Failed to open stdin");
stdin.write_all("Hello".as_bytes()).expect("Failed to write stdin");
```

本來用 spawn 的話子行程的 io 會繼承父行程的，相當於上面那行改成 .stdin(Stdio::inherit())，這裡我們改用 Stdio::piped() 把它接出來。  
接著我們可以從 p （型別是 process::Child）裡去取得它的 stdin, stdout, stderr，這個拿到的都是 Option 型別，用 expect 把它給解開來，裡面就會拿到 Rust 的 io 物件，
可以用呼叫對應[write 系列函式](https://doc.rust-lang.org/std/io/trait.Write.html)對它寫入內容，這裡用 write\_all 對 stdin 寫入 "Hello" 的 Vec<u8>。  
在 stdout 螢幕上就會看到 "olleH" 的輸出了。  

當然我們也可以在呼叫的時候把 stdout 也導向 piped 處理，讓我們讀出反轉的結果：  
```rust
let mut p = Command::new("rev")
    .stdin(Stdio::piped())
    .stdout(Stdio::piped())
    .spawn()
    .expect("rev command failed to start");

let stdin = p.stdin.as_mut().expect("Failed to open stdin");
stdin.write_all("Hello".as_bytes()).expect("Failed to write stdin");
let output = p.wait_with_output().expect("Failed to read stdout");
let revs = String::from_utf8_lossy(&output.stdout);
assert_eq!(revs, "olleH");
```

## 感想
以上大概就是 Rust std process 使用方法的整理了，我自己大概有三點感想：  

1. 用 Rust 寫其實沒有比 C 用 fork/exec 來寫來得簡單多少，畢竟我們就是要操作子行程，底層都是系統程式那套，Rust 頂多是封裝得比較完善一點，實際上用起來該設定的一個少不了。
2. 要寫系統程式，系統程式的概念少不了，要寫 process 至少需要知道作業系統行程的概念
（不然一不小心會變成 ~~World War Z~~ 殭屍產生器），操作輸入輸出需要大略知道 file descriptor 的概念，不然文件的繼承 stdin/stdout/stderr，piped 根本看不懂，不管你用哪套語言哪個作業系統，這些基本知識是逃不掉的。
3.  雖然如此，我覺得 Rust 仍然提供了一套不錯的封裝，在函式的回傳值上套用 Result/Option 的方式，
能有效提醒使用者可能發生的錯誤，並要求使用者必須處理他們，這點我認為是花了差不多的成本之後，Rust 唯一可以勝過 C 的地方。

不小心寫了落落長，如果你竟然看到這行了，希望這篇文章對你有幫助XD。