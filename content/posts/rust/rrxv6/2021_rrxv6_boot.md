---
title: "rrxv6 : riscv Hello World in OS"
date: 2021-07-03
categories:
- rust
- operating system
tags:
- rust
- xv6
- riscv
series:
- rrxv6
images:
- /images/rrxv6/loop.png
forkme: rrxv6
---

故事是這樣子的，大概六月中的時候，小弟因緣際會空出一些時間，因為武肺持續三級警戒只能待在家裡，除了打混摸魚之外順便看了一下別人寫的翻譯文
[embedonomicon](https://docs.rust-embedded.org/embedonomicon/preface.html)，翻完之後看看 rust cortex-m
[都被人做走了](https://github.com/rust-embedded/cortex-m)，那有什麼東西可以玩的呢？  
有一天晚上上床的時候就想到了，剛好最近在想看一下 MIT 教學用的作業系統 xv6，看看究竟可以用的作業系統是怎麼實作的，
而 xv6 本來是針對 x86 處理器，最近才被移植到新的 riscv 處理器上，
也有人把 xv6 [用 rust 重新實作](https://github.com/connorkuehl/xv6-rust) ，那我是不是能如下圖，填上這個表格最後一個空格呢？  
|   |C|Rust|
|:-|:-|:-|
|x86|[xv6 legacy](https://github.com/mit-pdos/xv6-public)|[xv6-rust](https://github.com/connorkuehl/xv6-rust)|
|Riscv|[xv6-riscv](https://github.com/mit-pdos/xv6-riscv)|**404 Not Found**|

<!--more-->

於是就我們這篇文啦，其實現在什麼屎都還沒弄出來，只用個不完整的手法 print 出一個 Hello World 而已，感覺自己挖了一個深不見底的坑（後面會看到為什麼），抖…。

總之讓我先做個整理，看看我這段時間都搞了什麼，以及未來的方向。

## 相關資源整理

### xv6-riscv
我用來參考的專案是 MIT 的 [xv6-riscv](https://github.com/mit-pdos/xv6-riscv)，已經將 xv6 遷移到 riscv 處理器上；不過這個專案有點沒在維護，在比較新的 qemu 上跑不起來，因此我改用[另一個人 fork 的版本](https://github.com/Crydsch/xv6-riscv)

### qemu
前述的問題，在 qemu v6 上面，對 riscv 已經實作了 Physical Memory Protection (PMP)，
而 MIT 的 xv6-riscv 沒有正確設定 PMP，在跳進 supervisor mode 的時候，存取記憶體就會觸動 PMP 導致處理器介入，
詳情[可見這篇修正](https://l1nxy.me/2021/05/26/fix-xv6-boot/)。  
簡而言之如果要用 MIT 的版本，就要用 qemu v5 進行除錯，我就是因為 archlinux 滾動式更新早早升上 qemu v6 才會踩到這個 bug。

### gcc
編譯 xv6-riscv 需要編譯器 riscv64-unknown-elf-gcc，這可以用套件管理進行安裝：
* Ubuntu: gcc-riscv64-unknown-elf
* Archlinux: AUR riscv64-unknown-elf-gcc

在 Ubunut/Archlinux 上，都有所謂的 linux-gnu gcc 可選，不過這裡不能用這個版本，請用 unknown-elf，或者 archlinux 上面還有更短的 riscv64-elf-gcc（其實我懷疑它就是 unknown-elf 只是省略 unknown）。  
參考 [osdev 的 Target_Triplet](https://wiki.osdev.org/Target_Triplet)，linux-gnu 假設了編出來的程式是在 Linux 上運作，可以用一些 Linux 提供的服務，我們自幹作業系統的話不會有這些東西。

gdb 就使用同一套的 riscv64-unknown-elf-gdb。

### rust
請使用 [rustup](https://rustup.rs/)，這會讓整個流程方便很多，在這篇文裡可以使用 stable 版本，未來 assembly 出現的時候會需要切到 nightly。

安裝好之後用 rustup 看看提供的 riscv 編譯目標。
```bash
$ rustup target list | grep risc
riscv32i-unknown-none-elf
riscv32imac-unknown-none-elf
riscv32imc-unknown-none-elf
riscv64gc-unknown-linux-gnu
riscv64gc-unknown-none-elf (installed)
riscv64imac-unknown-none-elf (installed)

$ rustup target install riscv64imac-unknown-none-elf
```

我經過許多試驗之後，選定的版本為 riscv64imac-unknown-none-elf，依據 [gentoo 的說明](https://wiki.gentoo.org/wiki/Project:RISC-V)，
意即 lp64，沒有 64gc (lp64d) 另外提供 floating point register，這在後面會遇到一些難解的問題。  

至於為什麼不針對 riscv32 開發……這真的是個好問題，我也還不知道要怎麼在程式碼上寫一次可以對應 32/64 的長度差異，
需要大神們出來救一下小弟，我目前都**只針對 riscv64 開發**。

### 文件相關

* Riscv spec 文件可從[官方網站](https://riscv.org/technical/specifications/) 
或是從 [Github](https://github.com/riscv/riscv-isa-manual) 下載，特別是 Volume 2, Privileged Spec，那是開機必看。
* Unprivileged Spec 裡面就是介紹處理器架構：暫存器、指令集 blahblahblah，
除非你是在寫很多 assembly 或是編譯器要查 manual，不然看一下其他 blog 的整理文，
像是[這篇關於一些指令](https://tclin914.github.io/16df19b4/) ，
跟[這篇關於暫存器](https://tclin914.github.io/77838749/) 應該就夠了。
* [five-embeddev 提供的網頁介面](https://www.five-embeddev.com/riscv-isa-manual/latest/priv-intro.html#introduction) 也非常好用。

## 作業系統的 Hello World

沒想到光整理資源就寫這麼多，總之讓我們開工，我的新 project 取名為 rrxv6，單純就是 rust riscv xv6，目前 code 已經先放上 [Github](https://github.com/yodalee/rrxv6)，但基本上還是個空殼。

這篇大概會做到之前[翻譯文的 reset_handler](https://yodalee.me/2021/06/2021_rust_bare_metal2_reset/) 的程度，
在 ARM 裡面，我們可以用全 rust 的寫法（雖然在 context switch 之類應該免不了要由 assembly 來處理各 register），但在 riscv 就不行了。

這是 ARM 跟 riscv64 架構差異所致，ARM 的設計規範，要把 initial stack top 的位址放在 0x0 ；reset handler 位址放在 0x4，
機器上電的時候就會自己去設定 stack top，然後跳進我們的函式執行，**因為 stack 已經設好了所以跳進 rust 函式不會有事**，
不然函式去動~~法喜充滿~~寫滿亂數的 sp 你看會不會出事。

riscv64 沒這麼自動，進去之後要先自己設定好 sp，這是 rust 函式做不到的。
我們先設定一個專案，做到所謂「作業系統的 Hello World」，也就是一個無窮迴圈。

### Rust code：
如先前在 [Rust 裸機程式系列](https://yodalee.me/series/rust-bare-metal-programming/)，先加上一個[空殼的 Rust 程式](https://yodalee.me/2021/06/2021_rust_bare_metal1_setting/)，除了 panic_handler 之外就是一個單純無窮迴圈的 start 函式。
```rust
// src/main.rs
#![no_std]
#![no_main]

use core::panic::PanicInfo;

#[no_mangle]
fn start() -> ! {
  loop{}
}

#[panic_handler]
fn panic(_panic: &PanicInfo<'_>) -> ! {
  loop {}
}
```

Cargo.toml 設定 panic 的時候直接無條件的 abort。
```toml
[profile.dev]
panic = "abort"

[profile.release]
panic = "abort"
```

### .cargo/config：

cargo 設定目標為前述的 riscv64imac-unknown-none-elf，在連結的時候使用 linker script linker.ld：
```
[build]
target = "riscv64imac-unknown-none-elf"

[target.riscv64imac-unknown-none-elf]
rustflags = ["-C", "link-arg=-Tlinker.ld"]
```

### build.rs

為了要和 assembly 一起編譯，我們別無選擇必須使用 [build script](https://doc.rust-lang.org/cargo/reference/build-scripts.html)
，它讓 rust 可以整合其他不同語言的編譯目標，例如 C, assembly 等等。

 在 Cargo.toml 裡面加上 cc 的 build-dependencies。
```toml
[build-dependencies]
cc = "1.0.25"
```

build.rs 的內容如下，讓它自動尋找 src/entry.S 來編譯：
```rust
use std::{env, error::Error, fs::File, io::Write, path::PathBuf};

use cc::Build;

fn main() -> Result<(), Box<dyn Error>> {
  // build directory for this crate
  let out_dir = PathBuf::from(env::var_os("OUT_DIR").unwrap());

  // extend the library search path
  println!("cargo:rustc-link-search={}", out_dir.display());

  // put `linker.ld` in the build directory
  File::create(out_dir.join("linker.ld"))?.write_all(include_bytes!("linker.ld"))?;

  // assemble the assembly file
  Build::new().file("src/entry.S").compile("asm");

  // rebuild if `entry.s` changed
  println!("cargo:rerun-if-changed=src/entry.S");

  Ok(())
}
```

當然，使用 build script 結合 assembly 不是沒有問題，如果上面設定目標設定為 riscv64gc-unknown-none-elf，在編譯的時候會出現如下的錯誤：
```txt
note: rust-lld: error:
/home/yodalee/os/rrxv6/target/riscv64gc-unknown-none-elf/debug/build/rrxv6-ceeee899b6717751/out/libasm.a(entry.o):
cannot link object files with different floating-point ABI
```
目前研判應該是編譯 assembly 的時候在 floating point 上的參數跟 rust 這邊不合，目前沒有解決方法，
所以我目標才選為 riscv64imac-unknown-none-elf。

### entry.S

我們的 entry.S 非常簡單，定義一個 _entry，裡面一個 jump 到我們 rust 的 start 函式裡；
start 函式只會 loop 所以有沒有設定 sp 都沒差；linker script section 設定為 .text.entry。
```asm
.section .text.entry
.global _entry
_entry:
  j start
```

### linker.ld

最後來到我們的 linker script，設定 ENTRY 為 assembly 裡面提供的 _entry；riscv 一上電的時候會從 0x8000_0000 的地方取指令來執行
（*先聲明我是看各討論區文章及 xv6-riscv 的實作得知這件事，我在規格書裡完全找不到相關描述，有知道出處的拜託一定告訴我QQ*）。  
因此我們在 SECTIONS 裡先把指針移到 0x8000_0000，依序寫入 *(.text.entry) 及其他的 .text，這個順序不能換，因為 _entry 一定要在 0x8000_0000。

```txt
OUTPUT_ARCH("riscv");
ENTRY(_entry);

SECTIONS
{
  . = 0x80000000;

  .text : {
    *(.text.entry);
    *(.text .text.*);
  }
};
```

## 編譯與執行
使用 cargo build 完成編譯，執行使用 qemu-system-riscv64 來執行，參數如下：
* -nographic 關掉圖形介面
* -smp 1 單核心執行，比較好除錯（我至今不知道多核心下如何好好 gdb）
* -machine virt 使用與平台無關的虛擬機
* -bios none 關掉 bios
* -S 讓 cpu 停在剛開始執行的時候
* -gdb tcp:3333 在 port 3333 上接受 gdb 連線，或者可用 -s 等同 -gdb tcp:1234
* -kernel blah 這串加上我們編譯出來的核心

put them together：
```bash
qemu-system-riscv64 -nographic -smp 1 -machine virt -bios none \
-S -gdb tcp::3333 -kernel target/riscv64imac-unknown-none-elf/debug/rrxv6
```

在另一個終端機打開 gdb，並輸入 `target remote :3333`，在 start 設定中斷點，就可以看到我們 *作業系統的 Hello World* 已經完成了。

![rrxv6 loop](/images/rrxv6/loop.png)

是的，Hello World 代表的是一個最基礎可以動的東西，一般程式是印出 Hello World；Machine Learning 可能是作線性迴歸；
我認為作業系統的 Hello World 就是進到一個無窮迴圈，這是所有作業系統的基礎，而看看這篇文章，這步通常比你想得還複雜。

本來，我是想一口氣直接寫完 riscv 的開機流程的，不過看這篇的份量，我看還是移到下一篇吧。
