---
title: "rrxv6 : stack pointer"
date: 2021-07-08
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
- /images/rrxv6/helloworld.png
forkme: rrxv6
---

上一篇我們成功讓 assembly 執行一個 jump 跳進 Rust 函式，但這樣其實一點用也沒有，畢竟只會 loop 的作業系統並不是一個很好的作業系統；
這篇我們就參考一下 xv6 的開機流程，然後試著用 Rust 重新實作。
<!--more-->

## xv6
首先先看到 xv6 的開機流程，依序是 `entry.S:_entry` -> `start.c:start`

```asm 
# entry.S
_entry:
  # set up a stack for C.
  # stack0 is declared in start.c,
  # with a 4096-byte stack per CPU.
  # sp = stack0 + (hartid * 4096)
  la sp, stack0
  li a0, 1024*4
  csrr a1, mhartid
  addi a1, a1, 1
  mul a0, a0, a1
  add sp, sp, a0
  # jump to start() in start.c
  call start
```
其實很簡單，就是設定好 sp ，然後就跳進去 start 裡面，stack0 的定義在 start.c 裡面。  
```c
__attribute__ ((aligned (16))) char stack0[4096 * NCPU];
```
在 riscv 裡，有為數眾多的 Control/Status Register (CSR)，名字一律以 m 開頭，只能用 csrr 跟 csrw 來讀寫，
mhartid 存的是 riscv 的 hart id，可以把 hart 想成一個硬體執行單元，id 規格中只保證一定要有一個 id 是 0，其他 id 連號還是亂跳都可以，
通常 id = 0 的單元就會身負重責大任，負責啟動作業系統核心。

```c
// start.c
unsigned long x = r_mstatus();
x &= ~MSTATUS_MPP_MASK;
x |= MSTATUS_MPP_S;
w_mstatus(x);

// set M Exception Program Counter to main, for mret.
// requires gcc -mcmodel=medany
w_mepc((uint64)main);

// disable paging for now.
w_satp(0);

// delegate all interrupts and exceptions to supervisor mode.
w_medeleg(0xffff);
w_mideleg(0xffff);
w_sie(r_sie() | SIE_SEIE | SIE_STIE | SIE_SSIE);

// ask for clock interrupts.
timerinit();

// keep each CPU's hartid in its tp register, for cpuid().
int id = r_mhartid();
w_tp(id);

// allow access to all physical memory by S mode
pmpinit();

// switch to supervisor mode and jump to main().
asm volatile("mret");
```

start.c 這邊就比較複雜了，雖然註解都有解釋了，下面還是條列式的解釋一下：

### 設定 mstatus register 的 MPP
我猜 MPP 意指 Machine Previous Privilege，riscv 可以有三種模式：
1. User Mode (0b00)
2. Supervisor Mode (0b01)
3. Machine Mode (0b11)

處理器實作可以選擇 MSU 三種模式都提供；提供 MU 兩種或只提供 M 模式的實作。  
可以想像在 User Mode 下，接到一個 interrupt 的時候，處理器就會升級到更高的權限，Previous Privilege 也會設為提升前的權限。  
因為 start 的最後會呼叫 mret 指令，從 machine mode 離開，
如果未設定 MPP 預設值為 0，就會進入 user mode ，設為 1 則會跳至 supervisor mode。

### 設定 mepc
當異常發生的時候，riscv 會自動把執行當下的 program counter 寫入 mepc 暫存器中，
可以想成我們的 start 就像在 reset exception handler 裡面，只是 mepc 處理器沒幫我們寫好，
所以這裡要自己填入等等呼叫 mret 之後處理器跳去的指令，也就是 main。

### 關掉 paging
由 satp register 控制

### 將 interrupt 跟 exception 都由 supervisor 來處理
riscv 有兩個暫存器 machine exception delegation (medeleg) 跟 machine interrupt delegation (mideleg) ，
寫入 1 的位元，就會把對應的 interrupt/exception 轉交由 supervisor mode 來處理，而不是如預設由 machine mode 處理。

### 設定 Supervisor interrupt enable
設定三個 bit ，讓：
1. Supervisor External Interrupt Enable (SEIE)
2. Supervisor Timer Interrupt Enable (STIE)
3. Supervisor Software Interrupt Enable (SSIE)

三種 Interrupt 都會啟動。

### 設定 timer interrupt
### 把 hart id 寫入 register x4 (tp) 中
### 設定 PMP
riscv 的 PMP 沒開的話，當我們一跳轉去 supervisor mode ，讀取指令時處理器就會介入，在 pmpinit 裡面，xv6 是把整塊記憶體都設為可 RWX。 

### 呼叫 mret
從 machine mode 跳轉到 MPP，也就是 Supervisor mode。

## 必要的實作

其實，如果要讓 main 動起來，只需要四個步驟：
1. 設定 MPP
2. 設定 mepc
3. 設定 PMP
4. mret

其他都是多餘的，只是為了後面的 kernel 部分鋪路，下面我們就來開工：

### 設定 sp

要設定 sp，我們要先開個空間作為程序的 stack，因為 riscv 設計上就支援多核心（你要說多 hart 也行），我們的 STACK0 的空間也要考慮到 NCPU。
```rust
// main.rs
#[no_mangle]
static STACK0: [u8;param::STACK_SIZE * param::NCPU] = \
  [0;param::STACK_SIZE * param::NCPU];
```

我們把設定參數都丟去 param.rs 裡：
```rust
// param.rs
pub const NCPU: usize = 8;
pub const STACK_SIZE: usize = 4096;
```


有了 STACK0，跟上面一樣設定 sp，注意我們這裡把 j start 換成 call start，因為現在有 stack ，
用 call 把暫存器 push/pop 到 stack 上也沒關係。  
這裡有一個問題，就是我不知道該怎麼讓 rust 跟 assembly 共用同一個變數，STACK_SIZE = 4096 這件事在 param.rs 跟 entry.S 都定義了一次，
顯然不太妙，但我也不知道怎麼做比較好。

```asm
.equ STACK_SIZE, 4096
_entry:
  la sp, STACK0
  li a0, STACK_SIZE
  csrr a1, mhartid
  addi a1, a1, 1
  mul a0, a0, a1
  add sp, sp, a0

  # jump to start() in start.rs
  call start
```

## Uart Hello World

其實 Rust 在寫嵌入式上真的是有點綁手綁腳，主因是 [Rust 與 asm 的整合](https://doc.rust-lang.org/beta/unstable-book/library-features/asm.html)
不是沒有，但都還未穩定化，這也是我[前一篇]({{<relref "2021_rrxv6_boot#rust">}})介紹工具時有說後面的程式會需要 nightly 的原因；
再來，Rust 的機車特性導致只要用了 `asm!` 執行 assembly，code 都必須要放在 unsafe block 裡面。

所以這段開機程式其實很好改寫，全部用 assembly 寫，然後就會變成滿滿的 unsafe 跟 asm!，然後 code 就會很醜。
我們可以先用 uart 小試牛刀，先聲明我這裡這樣寫是因為我只想先看到 Hello World，
這樣的uart 實作最終還是會被類似 cortex-m-semihosting 的手法換掉。

另外這段 uart 的 code 是參考**傳說中雄鎮金門衛我台海威震神州東南半壁的陳鍾誠教授**寫的 [mini-riscv-os](https://programmermedia.org/root/陳鍾誠/課程/系統程式/10-riscv/03-mini-riscv-os/01-HelloOs/doc.md)
，看了教授文章我才知道 qemu virt machine 在 0x1000_0000 有 default uart 可以用。

先從 uart 開始，我們可以使用 rust 的 [volatile_register](https://docs.rs/volatile-register/0.2.0/volatile_register/)
 映射一段記憶體位址，先定義 struct UART 內含八個 uart register，在函式內就能對這些 register 作讀寫，當然，實際的寫入都是 unsafe 行為。

```rust
// uart.rs
use volatile_register::{RW};

pub struct UART {
  thr: RW<u8>,
  ier: RW<u8>,
  isr: RW<u8>,
  lcr: RW<u8>,
  mcr: RW<u8>,
  lsr: RW<u8>,
  msr: RW<u8>,
  spr: RW<u8>,
}

impl UART {
  pub fn putc(&mut self, c: char) {
    while (self.lsr.read() & 0x40) == 0 {}
      unsafe { self.thr.write(c as u8); }
    }

  pub fn puts(&mut self, s: &str) {
    for c in s.chars() {
      self.putc(c);
    }
  }
}

pub fn read() -> &'static mut UART {
  unsafe { &mut *(0x1000_0000 as *mut UART) }
}
```

在 start 函式裡面我們就能像這樣呼叫印出 Hello World 了：

```
// main.rs
let m_uart = uart::read();
m_uart.puts("Hello World\n");
```

試試看：
![uart helloworld](/images/rrxv6/helloworld.png)

## 設定 CSR

以下是我用 rust asm! 完成，對應設定 mstatus 的 MPP 為 supervisor mode 的寫法。

```rust
/* Set M Previous Privilege mode to SupervisedMode
 * so mret will switch to supervise mode
 */
let mut x: u64;
unsafe { asm!("csrr {}, mstatus", out(reg) x); }
x &= !(3 << 11);
x |= (1 << 11);
unsafe { asm!("csrw mstatus, {}", in(reg) x); }
```

rust 的 asm 格式，就是用 asm 把要呼叫的指令文字包起來，例如：
```rust
asm!("nop");
```
有 input/output 的變數，則可用類似 format string 的方式，指令文字留下 {}，後面再加上 in(reg)/out(reg) 跟變數，整體來說是不難用啦。  
上面這段 code 會把 mstatus register 的 12,11 bits 設為 01，即 supervisor mode。

當然，這樣寫很 low，為什麼是 3<<11, 1<<11？兩個 unsafe 很礙眼？
下一章我們就來看看比較漂亮一點的寫法。（其實我本來想一章寫但這樣好像會太長）
