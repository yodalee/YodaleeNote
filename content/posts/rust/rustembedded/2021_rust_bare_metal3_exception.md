---
title: "在 2021 年要如何開發 Rust 裸機程式：分離核心與 exception handler"
date: 2021-06-21
categories:
- rust
- embedded system
tags:
- rust
- embedded system
series:
- rust bare-metal programming
images:
- /images/rust/rust_baremetal_debug_exception_handler.png
---

我們的最小程式現在能進到 reset_handler 了，但重要的是能進到使用者寫的 main 函式，不然這個 kernel 也沒用。
我們先把我們的 main.rs 改成 lib.rs，rt 編成 library 之後，類似 FreeRTOS 的感覺，再搭配使用者寫的 main.rs 編成完整的執行檔；
使用者寫的 main.rs 可以呼叫 kernel 提供的服務函式。
<!--more-->

## binary to library

```bash
mv src/main.rs src/lib.rs
```

新的 lib.rs 內容如下，移除開頭的 #![no_main]，library 也不管有沒有 main 函式：

```rust
#[no_mangle]
pub unsafe extern "C" fn reset_handler() -> ! {
  extern "Rust" {
    fn main() -> !;
  }

  main()
}

pub static RESET_VECTOR: unsafe fn() -> ! = reset_handler;
```

我們宣告了 extern 的 main 函式並在 reset_handler 呼叫它，因為我們外部的 main 函式會被判定為 unsafe 函式，
因此 reset_handler 跟 RESET_VECTOR 的型別都要加上 unsafe。

## build script

因為 linker 會搜尋 linker script 的位址，這個 linker script 是位在 kernel 而不是應用程式端，
這裡作者是使用 [build script](https://doc.rust-lang.org/cargo/reference/build-scripts.html)，把 linker.ld 加到編譯之中。

```rust
use std::{env, error::Error, fs::File, io::Write, path::PathBuf};

fn main() -> Result<(), Box<dyn Error>> {
  // build directory for this crate
  let out_dir = PathBuf::from(env::var_os("OUT_DIR").unwrap());

  // extend the library search path
  println!("cargo:rustc-link-search={}", out_dir.display());

  // put `linker.ld` in the build directory
  File::create(out_dir.join("linker.ld"))?.write_all(include_bytes!("linker.ld"))?;

  Ok(())
}
```

現在使用者可以另外開一個 project app，並提供 main 函式的實作，Cargo.toml dependancy 新增 rt：
```toml
[dependencies]
rt = { path = "../rt" }
```

把我們寫好的 cargo config 複製過來：
```bash
cp -r ../rt/.cargo .
```

本來 main.rs 的實作移到 app 的 main.rs

```rust
#![no_std]
#![no_main]

extern crate rt;

#[no_mangle]
pub fn main() -> ! {
    let _x = 42;

    loop {}
}
```

## 編譯測試

一樣在 app 內呼叫 cargo build 就可以編譯完成，用 objdump 觀看編譯結果：
```txt
arm-none-eabi-objdump -d target/thumbv7m-none-eabi/debug/app

target/thumbv7m-none-eabi/debug/app:     file format elf32-littlearm

Disassembly of section .text:

00000008 <main>:
   8:    b081          sub    sp, #4
   a:    202a          movs    r0, #42    ; 0x2a
   c:    9000          str    r0, [sp, #0]
   e:    2000          movs    r0, #0
  10:    b001          add    sp, #4
  12:    4770          bx    lr

00000014 <reset_handler>:
  14:    b580          push    {r7, lr}
  16:    466f          mov    r7, sp
  18:    f7ff fff6     bl    8 <main>
  1c:    defe          udf    #254    ; 0xfe
```

## type safety

原書裡有[一個小章節是在講 main 函式的 type safety issue](https://docs.rust-embedded.org/embedonomicon/main.html#making-it-type-safe)，
現在的寫法 app main 如果型別不是 fn() -> !，編譯仍然會通過，這會造成未定義行為。  
雖然為什麼編譯會過這件事實在很謎，但原書提供了一個 macro 的解法，讓 main 函式在定義時透過 macro 進行一次型別檢查。
不過它的做法會讓 reset_handler 到 main 之間多一次函式呼叫，變成 reset_handler -> main -> main mangled，
讓 rust 沒辦法像 C 這樣的簡潔，因此我這裡先略過這個實作。

## exception handler

在 Rust 上寫 Reset Handler，把 main 分離之後，這篇來處理其他的 handler 的部分，其實大同小異，不知道為什麼作者把這章放第四章了。

來看一下 Cortex M3 的圖，不知道為什麼官網的圖解析度超低，
這張是從[其他網站](https://www.programmersought.com/article/667781141/)取得的：

![cortexM3_resetvector](/images/rust/rust_baremetal_cortexm3_reset.jpg)

從 Reset 之後一路往上，就是 NMI（non-maskable interrupt）、Hard Fault、Memory Management Fault 等等，
也就是當這些 interrupt 發生時，處理器會終止目前執行的行程，從 reset vector 拿出處理函式的位址並跳過去執行，結束後再回到原本的行程。

我們希望 rt library 提供預設的實作，使用者若提供自己的實作則用使用者寫的：

```rust
extern "Rust" {
  fn nmi();
  fn hard_fault();
  fn mem_manage();
  fn bus_fault();
  fn usage_fault();
  fn svcall();
  fn pendsv();
  fn systick();
}

pub union Vector {
  reserved: u32,
  handler: unsafe fn(),
}

#[link_section = ".vector_table.exceptions"]
#[no_mangle]
pub static EXCEPTIONS: [Vector; 14] = [
  Vector { handler: nmi },
  Vector { handler: hard_fault },
  Vector { handler: mem_manage },
  Vector { handler: bus_fault },
  Vector { handler: usage_fault, },
  Vector { reserved: 0 },
  Vector { reserved: 0 },
  Vector { reserved: 0 },
  Vector { reserved: 0 },
  Vector { handler: svcall },
  Vector { reserved: 0 },
  Vector { reserved: 0 },
  Vector { handler: pendsv },
  Vector { handler: systick },
];

#[no_mangle]
pub fn default_exception_handler() {
  loop {}
}
```

先定義好 extern 的函式，並用 union Vector 讓函式與佔位的 u32 共用空間，以實作 reserved 的 interrupt；書裡的 extern 函式是用 C ABI 但目前應該沒差。
exception hander 就是一個長度 14，從 NMI 到 systick 的陣列，分段到區段 `.vector_table.exceptions`。
最後是預設的 exception handler，會進到無窮迴圈裡面。

## linker script

在 linker script ，reset_vector 之後就接著 exception handler，把 .vector_table.exceptions 區段放在這裡。

```txt
 .vector_table ORIGIN(FLASH) :
{
  LONG(ORIGIN(RAM) + LENGTH(RAM));
  KEEP(*(.vector_table.reset_vector));

  KEEP(*(.vector_table.exceptions));
} > FLASH
```

另外我們用 [PROVIDE](https://sourceware.org/binutils/docs/ld/PROVIDE.html) 把各 exception handler 
指定給 default_exception_handler，只要使用者沒有定義，就會由 linker 來提供符號定義。

```txt
PROVIDE(nmi = default_exception_handler);
PROVIDE(hard_fault = default_exception_handler);
PROVIDE(mem_manage = default_exception_handler);
PROVIDE(bus_fault = default_exception_handler);
PROVIDE(usage_fault = default_exception_handler);
PROVIDE(svcall = default_exception_handler);
PROVIDE(pendsv = default_exception_handler);
PROVIDE(systick = default_exception_handler);
```

## 測試
因為 QEMU 不能模擬 HardFault 或是 Memory access fault，我們只能切去 nightly version，並用 core::intrinsics 來產生一個 trap。
```rust
#![feature(core_intrinsics)]
#![no_main]
#![no_std]

extern crate rt;

use core::intrinsics;

#[no_mangle]
pub fn main() -> u32 {  !
  intrinsics::abort();
}
```

## 結果與除錯

使用 objdump 觀察反組譯的結果，main 會由 intrinsics::abort 發動一個 udf (permanently undefined) 指令，形成一個 hardfault exception。
```txt
arm-none-eabi-objdump -d --no-show-raw-insn target/thumbv7m-none-eabi/debug/app
00000040 <main>:
  40:    udf    #254    ; 0xfe
  42:    udf    #254    ; 0xfe

00000044 <reset_handler>:
  44:    push    {r7, lr}
  46:    mov    r7, sp
  48:    bl    40 <main>
  4c:    udf    #254    ; 0xfe

0000004e <default_exception_handler>:
  4e:    b.n    50 <default_exception_handler+0x2>
  50:    b.n    50 <default_exception_handler+0x2>
```

除錯的話也會看到程式走入 default_exception_handler：

![debug_exception_handler](/images/rust/rust_baremetal_debug_exception_handler.png)

使用 objdump 觀察 .vector_table section 的部分，除了 reset handler 是 0x44 之外，其他都指向 0x4e 的 default_exception_handler；reserved 的部分就留下 0x0 的 reserved word。
```txt
arm-none-eabi-objdump -s --section .vector_table target/thumbv7m-none-eabi/debug/app

target/thumbv7m-none-eabi/debug/app:     file format elf32-littlearm

Contents of section .vector_table:
 0000 00000120 45000000 4f000000 4f000000  ... E...O...O...
 0010 4f000000 4f000000 4f000000 00000000  O...O...O.......
 0020 00000000 00000000 00000000 4f000000  ............O...
 0030 00000000 00000000 4f000000 4f000000  ........O...O...
```

若使用者自行定義函式 hard_fault，就會看到 Hard Fault 的 exception handler 被設定給使用者定義的 hard_fault 函式了。