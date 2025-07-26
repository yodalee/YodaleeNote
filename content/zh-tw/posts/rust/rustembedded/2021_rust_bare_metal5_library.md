---
title: "在 2021 年要如何開發 Rust 裸機程式：函式庫"
date: 2021-06-23
categories:
- rust
- embedded system
tags:
- rust
- embedded system
series:
- rust bare-metal programming
images:
- /images/rust/rust_baremetal_helloworld.png
---

這應該是裸機程式的最後一篇了，回顧一下[第一篇]({{< relref "2021_rust_bare_metal1_setting.md" >}})所說，到現代幾個進化的點，
1. Rustup
2. cargo config
3. rlibc
4. 用 library

前三點我們已經看過了
1. 用 rustup 來安裝 target，雖然我後來想了一下，覺得這並不是 rust 勝過 C 而是 LLVM 勝過 gcc，rust 只是站在 LLVM 的肩膀上所以看得更遠而已。
2. cargo config 就如前文所述，利用 .cargo/config 來設定編譯目標，以及連結時的 linker script ，只要套用不同的 config 就能對不同目標編譯。
3. rlibc 可能比較隱晦一點，但 rlibc 要提供的 memset/memcpy/memmove ，在 core::ptr 裡面已經提供了核心的實作了，所以不需要再引入 rlibc。

最後就是用 library 啦，在前面的篇章都沒提到這個，為什麼？

<!--more-->

答案是，library 已經把我們前幾篇做的事情都做完了，如果是我們這次的目標，
rust 有個[小團隊 cortex-m-team](https://github.com/rust-embedded/wg#the-cortex-m-team) 在維護 
[cortex-m 函式庫](https://github.com/rust-embedded/cortex-m)：  
* reset_handler？library 已經寫好了，自己定義 main 吧。
* 要存取週邊？library 幫你封裝成 rust struct，呼叫對應的函式就好。
* cortex 的 semihosting？cortex-m 裡的 cortex-m-semihosting 可以處理這些。

所以說用了 library 之後前幾篇根本都不用寫了，最誇張的還有什麼，cortex-m team 還提供了 
[quickstart repository](https://github.com/rust-embedded/cortex-m-quickstart)，用
[之前提過的 cargo generate](https://yodalee.me/2021/05/1helloworld/) 把專案複製下來，改一改就可以用了，超級方便。

我們這邊就來給來 quickstart 一下：
```bash
cargo generate --git https://github.com/rust-embedded/cortex-m-quickstart
```

專案裡面，只需要以下幾個步驟：
1. 取得模板，如上面用 cargo generate 下載。
2. 修改 `.cargo/config` 裡面的編譯目標，我們跟之前一樣用 cortex_m3 的 thumbv7m-none-eabi。
3. 編輯 memory.x 裡面 flash 和 RAM 的起始位址和長度。
4. `cargo build`

基本設定完成。

## 修改
看一下它的 Cargo.toml，大致上就是需要下列相依：
```toml
cortex-m = "0.6.0"
cortex-m-rt = "0.6.10"
cortex-m-semihosting = "0.3.3"
panic-halt = "0.2.0"
```

cortex-m 是硬體虛擬化型別；cortex-m-rt 提供 runtime，也就是我們前幾篇做的：預設的 exception handler 等等；cortex-m-semihosting 則是 semihosting；panic-halt 提供 panic_handler。

把我們的 main 修改成這樣：
```rust
use cortex_m_semihosting::hprintln;

#[entry]
fn main() -> ! {
  hprintln!("Hello World");

  loop {}
}
```

跟前面一樣用 qemu 進去 debug，qemu 的參數記得加上 `-semihosting`，用 gdb 進去就能看到 "Hello World" 真的被印出來了：
![debug_helloworld](/images/rust/rust_baremetal_helloworld.png)

顯而易見，用上 cortex-m library 開發嵌入式程式的功夫簡化不少，目前來說最大的問題反而是 cortex-m 幾乎沒什麼文件跟使用案例
（cortex-m 裡面只有些許非常簡單的範例），想要使用也不知道怎麼用 Orz。

我想這系列文差不多就告一段落，這系統展現了 rust 的確有能力撰寫嵌入式系統的程式，雖然麻煩得多但不是不可能，
與四年前相比核心的支援也更加完善，我想就現實來看 rust 要能跟 C 競爭還需要一番功夫才行，
但 rust 也的確展現了如此的潛力，且讓我們期待未來的發展。 