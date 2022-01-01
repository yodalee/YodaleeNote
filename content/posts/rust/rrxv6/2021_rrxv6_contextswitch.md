---
title: "rrxv6 : Context Switch 與 Global Data"
date: 2021-07-20
categories:
- rust
- operating system
tags:
- rust
- xv6
- riscv
- static
series:
- rrxv6
forkme: rrxv6
---

首先先預告一下，這篇有可能會是本系列連續更新的最後一篇，更新完這篇之後我要去閉關念書（看 code）一段時間，原因我等等會說明。

上一篇我們提到在 rust 裡面實作實際對應實體暫存器的程式碼，同時也確定這些程式碼可以真的提供無額外成本的虛擬化，
這篇順著 mini-arm-os 的腳步，來實作 Context Switch；timer 的設定我們先跳過，畢竟這篇還不會實作到 timer interrupt 觸發 context switch。
<!--more-->

## struct Context
要實作 context switch 第一步就是要有 context 可以 switch，在 switch 的時候，riscv 需要存入以下的暫存器 `ra`, `sp`, `s0` - `s11`，因此我們先宣告 Context：
```rust
/// Saved Register for Context Switch
#[derive(Debug,Default,Clone,Copy)]
pub struct Context {
  /// return address and stack pointer
  pub ra:  u64,
  pub sp:  u64,

  /// Callee saved register
  pub s: [u64;12],
}
```

## Assembly Context Switch
另外需要 context switch 的 assembly，這段 code 跟傳說中陳鍾誠教授實作的 [mini-ricv-os](https://programmermedia.org/root/%E9%99%B3%E9%8D%BE%E8%AA%A0/%E8%AA%B2%E7%A8%8B/%E7%B3%BB%E7%B5%B1%E7%A8%8B%E5%BC%8F/10-riscv/03-mini-riscv-os/02-ContextSwitch/doc.md) 是一樣的：
```asm
.macro ctx_save base
  sd ra,  0(\base)
  sd sp,  8(\base)
  sd s0,  16(\base)
  sd s1,  24(\base)
  sd s2,  32(\base)
  sd s3,  40(\base)
  sd s4,  48(\base)
  sd s5,  56(\base)
  sd s6,  64(\base)
  sd s7,  72(\base)
  sd s8,  80(\base)
  sd s9,  88(\base)
  sd s10, 96(\base)
  sd s11, 104(\base)
.endm

.macro ctx_load base
  ld ra,  0(\base)
  ld sp,  8(\base)
  ld s0,  16(\base)
  ld s1,  24(\base)
  ld s2,  32(\base)
  ld s3,  40(\base)
  ld s4,  48(\base)
  ld s5,  56(\base)
  ld s6,  64(\base)
  ld s7,  72(\base)
  ld s8,  80(\base)
  ld s9,  88(\base)
  ld s10, 96(\base)
  ld s11, 104(\base)
.endm

.global sys_switch
.option norelax
.align 4
sys_switch:
  ctx_save a0
  ctx_load a1
  ret
```

## Global Mutable Data
現在來到整個 code 裡面最困難的地方了，我也不知道怎麼克服…。
故事是這樣子的，Rust 這個語言呢，對 static mut - 可變的 global 變數 - 就是嚴加看守，基本上程式設計師如果寫出 static mut 根本罪該萬死，
好死不死 static mut 似乎又是 embedded system/OS 必要的一環 - 你要怎麼讓整個作業系統都要存取的東西，比如說排程器 - 不是一個 static mut？

在 rust 裡面，如果你要用到 static 大概會有以下幾種做法：

### unsafe

這個方法就是簡單粗暴，什麼都不管直接寫就對了，我就是要用 static mut ，rustc 你走開。

我們宣告一個 user process 用的 Context
```rust
static mut CTX_PROC : Context = Context { ra:0, sp: 0, s:[0;12] };
```
這樣會有兩個問題，第一個是修改 static mut 會是 unsafe behavior，當 OS 要準備 context switch 的時候，
要分別寫入 ra 跟 sp register，就要寫在 unsafe 裡面：

```rust
unsafe {
  ctx_proc.ra = user_task,
  ctx_proc.sp = stack_proc,
}
```

這個做法的問題在，shared static 然後還 mut 在程式上就是許多問題的根源，這樣寫你的 code 裡面就會 unsafe 充滿~~賞心悅目~~，
很難確保程式不會出現競態條件。  
另外 rust 強制 static 變數在編譯的時候**必須**知道內容，這意味著 `std::default` 是沒辦法用的，就如上面我必須寫死 constructor `Context { / ... / }`，當 static 的物件複雜起來就有得受了。

### [Mutex](https://doc.rust-lang.org/std/sync/struct.Mutex.html)

合理的，如果你要宣告 global 變數就要放在 Mutex 裡面，用 `lock().unwrap()` 取得內部資料，再來就能做各種~~壞壞的事~~寫入的操作。  
可是呢，Mutex 在 std::sync，在我們這個 no_std 的環境當然是沒得用啦

### [lazy_static](https://docs.rs/lazy_static/1.4.0/lazy_static/)

這應該是 rust crate 上面下載量數一數二的專案了，它的本意是幫你把 static 的宣告跟初始化寫在一起，例如我的 Context 就可以寫：
```rust
use lazy_static::lazy_static;
lazy_static! {
  global ref CTX_OS: Context = Context::default();
}
```
這個 Context 的初始化會延遲到使用它的時候才呼叫，這讓我們可以把複雜資料結構的內容先寫好。  
but…跟第二點一樣，如果要生成可讀寫的資料，同樣要把 lazy_static 的資料放進 Mutex 裡面才行，不然 lazy_static 只是方便你生成 global data 的內容。

### [once_cell](https://docs.rs/once_cell/1.8.0/once_cell/)

看文件描述像 singleton 的封裝，不是很確定。
因為也是 std 才有（有 std 的話我就去用 Mutex 不用這個）所以直接跳過。

結論：234 都沒招，用第一種方法直接寫，我就 unsafe。
![iamunsafe](/images/rrxv6/Iamunsafe.png)

## Scheduler

要做到 cooperative multitasking ，我們至少要有空間給 task 的 stack 跟 context，我們把這團東西塞進 struct Scheduler 裡面，
NPROC 移植 xv6 的實作為 64 個 process：
```rust
type TaskStack = [u8;param::STACK_SIZE];
pub struct Scheduler {
  pub stack_task: [TaskStack;param::NPROC],
  pub ctx_task:   [Context;  param::NPROC],
  pub ctx_os:     Context,

  pub task_cnt:     usize,
  pub current_task: usize,
}
```

接著實作 scheduler 的 code，assembly 的函式用 extern 來宣告；這個 task_go 如果沒呼叫過 task_create 的話會出問題，但我沒打算修(欸
```rust
extern "Rust" {
  fn sys_switch(ctx1: *mut Context, ctx2: *mut Context);
}

impl Scheduler {
  pub fn task_create(&mut self, f: fn()) {
    let idx = self.task_cnt;
    let stack_top = &self.stack_task[idx] as *const u8 as u64 + ((param::STACK_SIZE-1) as u64);
    self.ctx_task[idx].sp = stack_top;
    self.ctx_task[idx].ra = f as u64;
    self.task_cnt += 1;
  }

  // switch to ctx_task[self.current_task]
  pub fn task_go(&mut self) {
    let mut ctx_os = &mut self.ctx_os;
    let mut ctx_new = &mut self.ctx_task[self.current_task];
    unsafe {
      sys_switch(ctx_os as *mut Context, ctx_new as *mut Context);
    }
  }

  // switch to ctx_os
  pub fn task_os(&mut self) {
    let mut ctx_os = &mut self.ctx_os;
    let mut ctx_now = &mut self.ctx_task[self.current_task];
    unsafe {
      sys_switch(ctx_now as *mut Context, ctx_os as *mut Context);
    }
  }

  pub fn advance(&mut self) {
    self.current_task = (self.current_task + 1) % self.task_cnt;
  }
}
```

雖然我們有實作了 `Scheduler::default()`，但對 global variable 來說沒用，我們只能手爆靜態的內容：
```rust
static mut SCHEDULER: Scheduler = Scheduler {
  stack_task: [[0;param::STACK_SIZE];param::NPROC],
  ctx_task:   [Context {
    ra:0, sp:0,
    s: [0;12] };param::NPROC],
  ctx_os:     Context{ ra:0, sp:0, s:[0;12] },
  task_cnt: 0,
  current_task: 0,
};
```

受限篇幅，讓我省掉 user_task1，只列出 user_task0，畢竟實作是一樣的，只是 uart 吐的字串不一樣：
```rust
pub fn user_task0() {
  let m_uart = uart::read();
  m_uart.puts("Task0 Created\n");

  unsafe { SCHEDULER.task_os(); }
  loop {
    m_uart.puts("Task0 Running\n");
    delay(10000);
    unsafe { SCHEDULER.task_os(); }
  }
}

pub fn user_init() {
  unsafe {
    SCHEDULER.task_create(user_task0);
    SCHEDULER.task_create(user_task1);
  }
}
```

可以看到無論是 task_create 還是 task_os，因為都是對 SCHEDULER 這個 global variable 的寫入，所以一定要加上 unsafe，這是 rust 的堅持無法逾越；
sys_switch 也是同理，函式進了 assembly 的所有權無法檢查，也要透過 unsafe 把它包起來。

執行起來，我們就能看到 cooperative multitask 的結果了：

```txt
OS: Activate next task
Task0 Running
OS: Back to OS

OS: Activate next task
Task1 Running
OS: Back to OS

OS: Activate next task
Task0 Running
OS: Back to OS

OS: Activate next task
Task1 Running
OS: Back to OS
```

看到這邊大家應該也累了，說實話 rust 在嵌入式系統上還是沒有 C/C++ 方便，特別是在嵌入式系統上至關重要的 global 變數，
在 rust 上面就是除非唯讀，不然近乎百分百禁止。  
我覺得這也是一個很好的思考，究竟對 OS 來說，最重要的、必須全系統都能存取的會是什麼？像在 FreeRTOS 的實作，
Context 也是在 process 產生的時候，才分配 Context 的記憶體，把這些不該 global 的東西都去掉，也許就是一個 OS 最核心的部分了。  

話說回來，我不相信能靠現在這套手爆 static 變數初始值的方式，實作出一套理想的 xv6 複製品，再來可能要花點時間研究一下，
像一些知名的 rust 嵌入式 OS 如 [tock os](https://www.tockos.org/) ，它們到底怎麼處理這樣的問題的呢？
根據初步調查，似乎有 [spin](https://docs.rs/spin/0.9.2/spin/) 之類的 library 提供 no_std 下面的 Mutex 功能，
再來看看能不能用在現在的實作上。

至於會不會到這篇就斷更爛尾……希望不要，畢竟在參加完 qcl 的婚禮前，小弟還不能停更啊（欸）。
