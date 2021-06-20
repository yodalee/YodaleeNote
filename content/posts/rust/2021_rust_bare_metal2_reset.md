---
title: "在 2021 年要如何開發 Rust 裸機程式：reset handler"
date: 2021-06-20
categories:
- rust
- embedded system
tags:
- rust
- embedded system
series:
- rust bare-metal programming
images:
- /images/rust/rust_baremetal_reset_debug.png
---

我們的目標先訂在 arm cortex m3 的處理器，
m3 處理器參考 [arm 官方的開發文件](https://developer.arm.com/documentation/dui0552/a/the-cortex-m3-processor/exception-model/vector-table)，
在 arm 處理器一上電的時候，會從記憶體位址 0x0 的地方讀取兩個值：
1. 0x0 是初始的 stack pointer value。
2. 0x4 是 reset exception handler。
<!--more-->

處理器會拿了 stack pointer value 寫入 SP register，然後跳到 reset exception handler 的位址開始執行；其他種類的 exceptions handler，則是依序排列在後。  
在裸機程式上，我們必須用 [linker script](https://yodalee.me/2015/04/2015_linkerscript/) 來分配各區塊要放在哪裡，包括編譯出來的 code、程式要用的 data，靜態變數等等。  
除了 linker script，在 rust 原始碼，我們也需要用 attribute 的方式，指定某些特定的函式編譯過後的 symbol 名稱以及目標的區段，包括：
* #[no_mangle] 關閉函式、變數的[名稱修飾 name mangling](http://swaywang.blogspot.com/2011/10/cname-mangling.html)，函式名字是什麼，編譯完就是什麼，而不是 rust 修飾過那一長串看不懂的文字。
* #[export_name = "foo"] 指定編譯完的符號名就是 foo。
* #[link_section = ".bar"] 指定編譯完的符號會放在 .bar 區段。

## Rust reset_handler

stack pointer 初始化我們交給 linker script，先在 rust 加上 reset handler：

```rust
// src/main.rs
#[no_mangle]
pub fn reset_handler() -> ! {
  let _x = 42;
  loop {}
}

#[link_section = ".vector_table.reset_vector"]
#[no_mangle]
pub static RESET_VECTOR: fn() -> ! = reset_handler;
```

RESET_VECTOR 就是指向 reset_handler 的 pointer，MCU 上電之後第一個執行的函式，從這個函式回傳會是未定義行為，
因為 stack 裡面也沒有上一個函式可以回傳。我們把 reset_handler 的回傳[設為 `!` 表示不會回傳的函式]({{< relref "2018_rust_cparser" >}})。  
書裡的 reset_handler 跟 RESET_VECTOR 的型態是用 `unsafe extern "C" fn() -> !`，指定是 unsafe 函式並用 C ABI，
但我試過用 Rust ABI 也沒問題，unsafe 目前還不需要，未來視函式實作有 unsafe behavior 的時候要加上去。

這裡我們實作了 reset_handler 函式，RESET_VECTOR 則是它的 pointer，指定這個 pointer 的區段為 .vector_table.reset_vector，
為了讓 linker 可以看到這個符號，函式與指標都要加上 pub。

## linker script

先增檔案 linker.ld，並新增以下內容（可惡大概 linker script 太冷門 hugo 沒有上色）：

```txt
MEMORY
{
  FLASH : ORIGIN = 0x00000000, LENGTH = 256K
  RAM : ORIGIN = 0x20000000, LENGTH = 64K
}

/* The entry point is the reset handler */
ENTRY(reset_handler);

EXTERN(RESET_VECTOR);

SECTIONS
{
  .vector_table ORIGIN(FLASH) :
  {
    /* initial Stack Pointer value */
    LONG(ORIGIN(RAM) + LENGTH(RAM));

    /* reset vector */
    KEEP(*(.vector_table.reset_vector));
  } > FLASH

  .text :
  {
    *(.text .text.*);
  } > FLASH

  /DISCARD/ :
  {
    *(.ARM.exidx .ARM.exidx.*);
  }
}
```

### MEMORY
在 memory 指定硬體平台的 FLASH 和 RAM 分別的起始位置和長度，這會對應到實際的 FLASH 和記憶體位址。

### ENTRY
指定 reset_handler 函式是我們程式的進入點，因為 linker 會激進地把沒用的東西都丟掉，沒加這行連 reset_handler 都會被 linker 丟掉，
~~linker：當我瘋起來連我自己都會怕~~用 ENTRY 保留 reset_handler 以及所有它呼叫到的函式。

### EXTERN
linker 的運作是這樣，讀入所有輸入的 .o 檔之後，從 ENTRY 函式開始搜尋所有可見的符號，其餘沒被找到的就丟棄掉；
EXTERN 告訴 linker 還有一個外部來的符號，讓 linker 除了 ENTRY 會也要保留 EXTERN 指定的符號。

### sections

這部分切成三個區塊：.vector_table、.text 及被丟棄的其他。

.vector_table 我們指定必須從 ORIGIN(FLASH) 開始放起，內含兩個條目：
1. 因為 ARM stack 的成長方向是往下長，由上面 MEMORY 區段指定的 RAM ，算出 RAM 的頂端，作為 initial stack pointer。
2. 我們保留區段 .vector_table.reset_vector 的內容，也就是 RESET_VECTOR 的所在。

.text 是剩餘的程式碼，reset_handler 的實作會在這裡。

/DISCARD/ 就是剩餘不需要的部分，這是跟 ARM unwinding stack 相關的部分，把它們丟了。

## config

編譯時可以由 cargo 指定 linker script，但跟 target 一樣太麻煩了，我們直接加在 `.cargo/config` 裡：
```toml
[build]
target = "thumbv7m-none-eabi"

[target.thumbv7m-none-eabi]
rustflags = ["-C", "link-arg=-Tlinker.ld"]
```

指定在編譯 thumbv7m-none-eabi 的時候，使用 linker.ld 作為 linker script，這樣就能編譯成功啦。

## 結果

讓我們來檢視一下編譯結果，使用 objdump 反組譯程式，可以看到 reset_handler ，移動 sp 空出 _x 的空間，在裡面存入 42，然後開始無窮迴圈；
其實我個人比較好奇編譯器怎麼沒有把 _x = 42 這段給最佳化掉：
```txt
$ arm-none-eabi-objdump -d target/thumbv7m-none-eabi/debug/rt

target/thumbv7m-none-eabi/debug/rt:     file format elf32-littlearm

Disassembly of section .text:

00000008 <reset_handler>:
   8:    b081          sub    sp, #4
   a:    202a          movs    r0, #42    ; 0x2a
   c:    9000          str    r0, [sp, #0]
   e:    e7ff          b.n    10 <reset_handler+0x8>
  10:    e7fe          b.n    10 <reset_handler+0x8>
```
另外是 section 的部分：
```txt
$ arm-none-eabi-objdump -s --section .vector_table target/thumbv7m-none-eabi/debug/rt

target/thumbv7m-none-eabi/debug/rt:     file format elf32-littlearm

Contents of section .vector_table:
 0000 00000120 09000000                    ... .... 
```

因為是 little endian，第一個 4 bytes 是 0x20010000，第二個是 0x00000009。  
* 0x2001_0000 正是我們指定的 0x20000000 + 64K (2^16) 的位址。
* 0x0000_0009 則對應上面 reset_handler 的位址 0x00000008，LSB 的 1 表示跳過去之後會執行 arm thumb mode。

## 實際測試
可以使用 qemu 進行實際測試（用 Ctrl+A, X 來關掉 qemu）：
```bash
qemu-system-arm \
  -cpu cortex-m3 \
  -machine lm3s6965evb \
  -gdb tcp::3333 \
  -S -nographic \
  -kernel target/thumbv7m-none-eabi/debug/rt
```

並使用另一個終端機進行除錯：
```bash
arm-none-eabi-gdb -q target/thumbv7m-none-eabi/debug/rt
```

![debug reset kernel](/images/rust/rust_baremetal_debug_reset.png)
這個畫面怎麼文字還會溢出畫面啦 Orz。

漂亮。