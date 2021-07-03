---
title: "在 2021 年要如何開發 Rust 裸機程式：設定與空殼"
date: 2021-06-19
categories:
- rust
- embedded system
tags:
- rust
- embedded system
series:
- rust bare-metal programming
---

~~其實標題應該要寫成「在 2021 裡用 Rust 開發裸機程式是種怎樣的體驗」~~

故事是這樣子的，很久很久以前我曾經[寫過一篇文]({{< relref "2016_rust_arm_helloworld" >}})，
胡亂攪了一陣，弄出一個只是會動的 Rust 嵌入式系統，時隔這麼久，Rust 的生態也完全不一樣了，最近因為剛好比較閒就花了點時間再看看，
結果找到別人[連書都寫好了呢](https://docs.rust-embedded.org/embedonomicon/preface.html)w （看書中的 rustc 成書年代應該是 2018 年左右）。

這篇大概會是照著上面這本書的操作記錄，不知道會整理成多少篇，讓我們拭目以待。

<!--more-->

大家可以先回頭看一下之前發過的文，從那時候到現在，改變最多如下：
1. Rustup：舊文裡還要寫一堆 json 的目標設定檔，現在都不用，用 Rustup 直接安裝 target 幾秒內完成（如果是 rustup 未支援的話還是要自己寫啦）。
2. 使用 cargo config，可以操控 cargo 編譯指定的 target，就不用像文中指令都要瘋狂寫一堆根本記不起來的參數
3. [rlibc](https://github.com/alexcrichton/rlibc) deprecated：現在 compiler 會自動提供 memset, memcopy, memmove 等必要的函式，不用 rlibc 了
4. 用 library 不要手刻介面：直接存取硬體位址在 rust 一律是 unsafe 的行為，library 會封裝這些行為讓你更方便存取週邊裝置，
現今的 library 更完善，由團隊來維護，不像過去是由個別開發者所貢獻。

## 設定

先從 rustup 開始，rustup target list 可以列出目前 rust 支援的所有 target，要安裝跟移除可用
```bash
rustup target install <target>
rustup target remove <target>
```
即完成目標的安裝/移除，超級簡單，這點甚至比寫 C 的時候還要裝特別編譯的 gcc 還要簡單，常用的 arm 例如 arm-none-eabi-gcc ，
在 archlinux 上可以直接用套件包 pacman 安裝，但特殊的就不行，像是 arm-linux-gnueabihf ，
要用 AUR 從頭編譯整套 gcc，沒設定好直接浪費幾個小時在編譯，用 rustup 管理 target 是**我第一次覺得 Rust 在嵌入式系統有超越 C 的地方**。

以下是我的設定：

```bash
$ rustup default stable
$ rustc -V
rustc 1.52.1 (9bc8c42bb 2021-05-09)
$ rustup target add thumbv7m-none-eabi
```

另外要安裝 qemu-system-arm 跟 arm-none-eabi-gdb ，應該都可以用套件管理來安裝。

就這樣！~~南北設定一起串聯~~設定就這麼簡單。

## 最小的程式
平常我們在 OS 上面寫 rust 程式，一定用了很多 rust std 提供的功能，std 則假定由作業系統提供了許多的服務：執行緒、行程、檔案系統等等；
std 之外則是 rust core，core 提供環境以外，和語言相關的基本操作，像型別如 float, string, slice，  原子操作等等。  
我們最小的程式（bare-metal 一般好像翻裸機）只會用個 core 的功能，std 用 #![no_std] 把 std 拿掉，
只要寫的是裸機如作業系統核心、韌體、bootloader 都不會有 std 功能可以使用。

```bash
$ cargo new rt
```

開一個空白 project 之後，編譯預設的 main.rs 檔案：

```rust
// src/main.rs
#![no_std]
#![no_main]

use core::panic::PanicInfo;

#[panic_handler]
fn panic(_panic: &PanicInfo<'_>) -> ! {
    loop {}
}
```

#![no_std] 上面有解釋過了。  
#![no_main] 表示這支 rust 程式不會有一般的 main，一般 main 就會假定有 command line argument ，裸機程式上也沒有這種東西。  
#[panic_handler] 則是設定程式 panic 的時候會呼叫的函式，在呼叫 core::panic! 的時候會呼叫這個函式。  

### eh_personality
在有些 target 上，panic 的時候不會無條件的 abort，這時候可以
1. 告訴 cargo 我就是要這樣無條件 abort。
2. 新增一個 eh_personality 函式。

eh_personality 的介紹，可以參考官方文件的[介紹章節](https://doc.rust-lang.org/unstable-book/language-features/lang-items.html#more-about-the-language-items)，以下節錄：
> The first of these functions, rust_eh_personality, is used by the failure mechanisms of the compiler. This is often mapped to GCC's personality function (see the libstd implementation for more information), but crates which do not trigger a panic can be assured that this function is never called.

套用第一種解法，我們在 Cargo.toml 裡面加上這幾行
```toml
[profile.dev]
panic = "abort"

[profile.release]
panic = "abort"
```
第二種解法，要自己提供 eh_personality 的實作，但這個必須使用 nightly 的編譯器，才能使用 language items：
```rust
#![feature(lang_items)]

#[lang = "eh_personality"]
extern "C" fn eh_personality() {}
```

## 編譯
使用 cargo build，並搭配 --target 指定編譯為 thumbv7m-none-eabi：
```bash
cargo build --target thumbv7m-none-eabi
```

為了不要每次編譯都要下這麼長一串，我們可以編輯檔案 .cargo/config：
```toml
[build]
target = "thumbv7m-none-eabi"
```

之後就可以直接下 cargo build 了。

## 結果
我們的編譯結果為 `target/thumbv7m-none-eabi/debug/rt`。  
可以用 size 檢查執行檔各區段的大小，會發現裡面什麼都沒有，用 gdb 進去看的話，就連單步執行都會出現 `Cannot find bounds of current function` 的錯誤：  

```bash
$ arm-none-eabi-size target/thumbv7m-none-eabi/debug/rt
```
```txt
   text       data        bss        dec        hex    filename
      0          0          0          0          0    target/thumbv7m-none-eabi/debug/rt
```

不過從編譯出來的 object 檔，又可以看到的確有 panic 相關的符號在裡面：
```bash
$ rustc --target thumbv7m-none-eabi --emit=obj src/main.rs
$ arm-none-eabi-nm main.o
00000000 T rust_begin_unwind
```

不過，這是個起頭，後面就要對這個 main.rs 新增東西，讓程式更完善了。
