---
title: "rrxv6 : Embedded Rust"
date: 2021-07-12
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
- /images/rrxv6/mstatus.png
forkme: rrxv6
aliases:
- /2021/07/2021_rrxv6_embedded_rust
---

上一回我們看到我們用 rust 寫了一些底層的 code，當然，這個寫法並不好看，有沒有更漂亮的寫法呢？
這篇參考了 rust [cortex-m](https://github.com/rust-embedded/cortex-m) 的寫法，
以及強者我同學在 Google 大殺四方的小新大大分享的文 [A guide to better embedded C++](https://mklimenko.github.io/english/2018/05/13/a-guide-to-better-embedded/)。
<!--more-->

簡單來說，我們要把所有的 register 都封裝起來，然後把原本的位元操作虛擬化（abstraction），讓我們可以從更高層次看待硬體的行為、對硬體操作；
這個實作必須要是零成本（zero cost abstraction），也就是說有/沒有虛擬化產生的 code 應該要一樣好，不會有多餘的 cost。

# Register Abstraction

以上一篇的 Mstatus 為例，這是本來的 code，讀出 mstatus CSR 的值、將 D12..D11 設成 0b01 再寫回 mstatus 中。
```rust
let mut x: u64;
unsafe { asm!("csrr {}, mstatus", out(reg) x); }
x &= !(3 << 11);
x |= (1 << 11);
unsafe { asm!("csrw mstatus, {}", in(reg) x); }
```

這段 code 有個問題，在於它很難懂也難以維護，過一段時間不看文件再看 code 就看不懂了，讓我們參考 rust cortex-m 的作法：

```rust
pub struct Mstatus {
  bits: u64,
}
```

這個 struct Mstatus 封裝了 mstatus 這個 register，讓我們先新增一些 method 跟 read/write 兩個實際讀寫 register 的介面：
```rust
impl Mstatus {
  #[inline]
  fn bits() -> u64 { self.bits }

  #[inline]
  fn from_bits(bits: u64) -> Self {
    Self { bits }
  }

  #[inline]
  fn read() -> Self {
    let bits: u64;
    unsafe {
      asm!("csrr {}, mstatus", out(reg) bits);
    }
    Self { bits }
  }

  #[inline]
  fn write(self) {
    let bits = self.bits();
    unsafe {
      asm!("csrw mstatus, {}", in(reg) bits);
    }
  }
}
```

下一步我們要把設定 bits 的行為封裝起來，來看一下 mstatus 的 bit field 的設定：

![mstatus](/images/rrxv6/mstatus.png)


要設定的是 MPP D12..D11，共有三種（視處理器實作而定）不同的模式：
* Machine Mode: 0b11
* Supervisor Mode: 0b01
* User Mode: 0b00

三種模式可以輕鬆虛擬化為 enum
```rust
enum Mode {
  MachineMode,
  SupervisorMode,
  UserMode,
}
```

設定 MPP 這個單一的行為也封裝進函式裡：
```rust
impl Mstatus {
  #[inline]
  pub fn get_mpp(self) -> Mode {
    if (self.bits >> 11) & 3 == 3 {
      Mode::MachineMode
    } else if (self.bits >> 11) & 3 == 1 {
      Mode::SupervisedMode
    } else {
      Mode::UserMode
    }
  }

  #[inline]
  pub fn set_mpp(&mut self, mode: Mode) {
    self.bits &= !(3 << 11);
    self.bits |= match mode {
      Mode::MachineMode =>    (3 << 11),
      Mode::SupervisedMode => (1 << 11),
      Mode::UserMode =>       (0 << 11),
    }
  }
}
```

設定 mstatus 的 code 就能改寫為：
```rust
let mut ms = mstatus::read();
ms.set_mpp(mstatus::Mode::SupervisedMode);
mstatus::write(ms);
```
意圖明顯不少。

# Zero Cost Abstraction

當然，如此實作是否會帶來對應的成本？答案是不會。  
這個不能看 debug code ，我真的反組譯，完全沒最佳化的 Rust build 簡直~~比豬血糕香菜披薩還要~~悲劇，一堆 jump 還 jump 到它的下一個指令，
上面的 read/set_mpp/write 真的都生成 function call。  
讓我們直接反組譯 release code：
```txt
riscv64-unknown-elf-objdump -d target/riscv64imac-unknown-none-elf/release/rrxv6

80000022: 30002573            csrr  a0,mstatus
80000026: 75f9                  lui a1,0xffffe
80000028: 7ff5859b            addiw a1,a1,2047
8000002c: 8d6d                  and a0,a0,a1
8000002e: 6585                  lui a1,0x1
80000030: 8005859b            addiw a1,a1,-2048
80000034: 8d4d                  or  a0,a0,a1
80000036: 30051073            csrw  mstatus,a0
```

這個結果跟 gcc 在 xv6-riscv 上面編譯出來的結果，是完全一模一樣的（register 不一樣），函式都 inline 了，
就算你不加 `#[inline]` rustc/LLVM 還是會很自動的幫你 inline：
1. csrr 讀出 mstatus
2. lui + addiw => !(3 << 11)
3. lui + addiw => (1 << 11) 雖然我不知道為什麼準備一個 2048 要這麼麻煩
4. csrw mstatus 寫入

# 其他的 register
同樣的概念可以類推到其他的 register，例如 supervisor interrupt enable (sie)：

![sie](/images/rrxv6/sie.png)

同樣經過上面的改寫，我們在 start 裡面會這樣寫，設定 D9, D5, D1 為 0b1：
```rust
let mut sie = sie::Sie::read();
sie.set_supervisor_enable(Interrupt::SoftwareInterrupt);
sie.set_supervisor_enable(Interrupt::TimerInterrupt);
sie.set_supervisor_enable(Interrupt::ExternalInterrupt);
sie.write();
```

最佳化之後，直接 or 546 = 0x222 無負擔，真是太神奇啦傑克：
```txt
80000056: 10402573            csrr  a0,sie
8000005a: 22256513            ori a0,a0,546
8000005e: 10451073            csrw  sie,a0
```

換個角度來說，我們這個寫法讓 code 好理解一些，人類腦袋少動一點，代價就是操壞編譯器，~~不過反正 rust 編譯本來就夠慢了再慢一點也沒差~~。

# start

全部的 register 都這樣做過一輪之後，rust 寫的 start 函式會像這樣：

```rust
use core::panic::PanicInfo;

use crate::{csrr, csrw};

use crate::param;
use crate::riscv::register::mstatus;
use crate::riscv::register::mepc;
use crate::riscv::register::tp;
use crate::riscv::register::hartid;
use crate::riscv::register::delegate;
use crate::riscv::register::sie;
use crate::riscv::register::interrupt::Interrupt;
use crate::riscv::register::pmp::{PMPConfigMode,PMPConfigAddress,PMPAddress,PMPConfig};

#[no_mangle]
fn start() -> ! {
    extern "Rust" {
        fn main() -> !;
    }

    /* Set M Previous Privilege mode to SupervisedMode
     * so mret will switch to supervise mode
     */
    let mut ms = mstatus::read();
    ms.set_mpp(mstatus::Mode::SupervisedMode);
    mstatus::write(ms);

    // Setup M exception program counter for mret
    let m_mepc = mepc::Mepc::from_bits(main as u64);
    mepc::write(m_mepc);

    // Disable paging for now
    let x = 0;
    csrw!("satp", x);

    // Delegate all interrupts and exceptions to supervisor mode
    delegate::medeleg::write(0xffff);
    delegate::mideleg::write(0xffff);

    // Enable interrupt in supervisor mode
    let mut sie = sie::Sie::read();
    sie.set_supervisor_enable(Interrupt::SoftwareInterrupt);
    sie.set_supervisor_enable(Interrupt::TimerInterrupt);
    sie.set_supervisor_enable(Interrupt::ExternalInterrupt);
    sie.write();

    // Store hart id in tp register, for cpuid()
    let hartid = hartid::Mhartid::read().bits();
    tp::write(hartid);

    // Setup PMP so that supervisor mode can access memory
    PMPAddress::write(0, (!(0)) >> 10);

    let mut config = PMPConfig::from_bits(0);
    config.set_config(PMPConfigMode::Read);
    config.set_config(PMPConfigMode::Write);
    config.set_config(PMPConfigMode::Exec);
    config.set_config(PMPConfigMode::Address(PMPConfigAddress::TOR));
    PMPConfig::write(config);

    // Switch to supervisor mode and jump to main
    unsafe { asm!("mret"); }

    // mret will jump into kernel, should not execute to here
    loop {}
}
```

這樣設定過後，我們終於成功進到 main 函式了。

# 結語

為什麼我[第一篇]({{<relref "rrxv6_boot.md" >}})會說：

> 感覺自己挖了一個深不見底的坑

因為 riscv 不知道為什麼 csr 超級多，按照 spec 來看可以多到 4096 個，根本不是 Cortex-m 那少少幾個可以比的，
要我重寫 xv6 幾乎就是要我做一套 riscv library，把全部的 csr 都虛擬化。  
雖然有測試了一個動用 rust macro 的寫法，能自動產生上述 read/write 等固定的部分，如果成功的話當然是能省下非常多手刻的部分，
但我看個別 register 的細部行為，還是會需要大量人工，那我還不累死…。
