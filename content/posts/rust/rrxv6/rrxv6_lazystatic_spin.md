---
title: "rrxv6 : spin mutex"
date: 2021-07-24
categories:
- rust
- operating system
tags:
- rust
- xv6
- riscv
- lazy_static
- spin
series:
- rrxv6
forkme: rrxv6
aliases:
- /2021/07/2021_rrxv6_lazystatic_spin/
---

故事是這樣子的，上一篇我們使用 unsafe 來操作 global variable，並用這個做到 cooperative multitask，
很不幸的這個方法是不行的，包括幾個問題：
1. 身為 Rustacean 非不得已怎麼可以用 unsafe 呢？這樣狂用 unsafe 根本離經叛道
2. 當 static 的型態複雜到一個程度的時候，這樣手爆資料型態絕不是方法，一定要使用 default 才行。

稍微搜尋一下之後，果然找到一個可行的方案，用社群提供的 crate [spin](https://docs.rs/spin/0.9.2/spin/) ，
可以在 `#[no_std]` 的狀況下提供 Mutex（有關如何實作 Rust Mutex，'
可以參見[這篇文章](https://mnwa.medium.com/building-a-stupid-mutex-in-the-rust-d55886538889) ）
<!--more-->

立馬嘗試了一下 spin Mutex，到最後的確有把 code 寫出來，不過中間經過一段曲折的除錯過程，讓我折騰了一段時間；
這篇文就來看看要怎麼用 spin 跟 lazy_static 改善上一篇的 code ，以及一半的除錯經驗吧。

# 引入 Spin 與 lazy_static
先在 Cargo.toml 裡面加上兩個套件相依，lazy_static 要加上 features spin_no_std，這樣它會改成用 no_std 的實作：
```toml
lazy_static = { version = "1.4.0", features = ["spin_no_std"] }
spin = "0.9.2"
```

有了這兩個聯手，static mut Scheduler 就能改成使用 Default ，看起來乾淨不少：
```rust
use lazy_static::lazy_static;
use spin::Mutex;

lazy_static! {
  static ref SCHEDULER: Mutex<Scheduler> = Mutex::new(Scheduler::default());
}

impl Default for Scheduler {
  fn default() -> Self {
    Self {
      ctx_task:   [Context::default();param::NPROC],
      ctx_os:     Default::default(),

      task_cnt: 0,
      current_task: 0,
    }
  }
}
```

使用的時候，對 SCHEDULER 呼叫 lock 就能從 Mutex 裡取出包著的物件，重點是內含物件是可寫入的；
Mutex 在離開所在的 scope 時，就會自動 unlock，函式如 task_create 可改寫如下：

```rust
pub fn task_create(f: fn()) {
  let mut scheduler = SCHEDULER.lock();
  let idx = scheduler.task_cnt;
  let stack_top = (&STACK_TASK[idx]).as_ptr() as u64 + ((param::STACK_SIZE - 1) as u64);
  scheduler.ctx_task[idx].sp = stack_top;
  scheduler.ctx_task[idx].ra = f as u64;
  scheduler.task_cnt += 1;
}
```

可以看到我們用 `SCHEDULER.lock()` 取得內含的 scheduler，再來要怎麼修改內容都沒問題。  
跟上一篇不同之處，我把 stack_task 從 Scheduler 搬出去，變成 static （沒有 mut）變數了，原因後述。

另外 task_go 的改寫則如下：
```rust
pub fn task_go(i: usize) {
  let (ctx_os,ctx_new) = {
  let mut scheduler = SCHEDULER.lock();
  (&mut scheduler.ctx_os as *mut Context,
   &mut scheduler.ctx_task[i] as *mut Context)
  };
  unsafe {
    sys_switch(ctx_os, ctx_new);
  }
}
```

sys_switch 因為是 assembly code 仍然需要加上 unsafe；為什麼取出 ctx_os, ctx_new 要用這種奇怪的寫法，
這是因為 Mutex 的 lock 只有到 **scope end** 也就是 `}` 才會 unlock，但是 task_go 在進行到 sys_switch 的時候就 context switch 到其他 task 了，
因此 Mutex 並沒有 unlock，下一刻當 user_task 呼叫 task_os 試著鎖定 Mutex 時就會拿不到 lock，然後就 deadlock 了；
為了強制 Mutex 解鎖，就得把它包進一層 scope 裡面，最後就變成這奇怪的樣子。

當然這還不是最醜的，最醜的是 main loop：
```rust
loop {
  m_uart.puts("OS: Activate next task\n");
  let idx = {
    let scheduler = SCHEDULER.lock();
    scheduler.current_task
  };
  task_go(idx);
  {
    let mut scheduler = SCHEDULER.lock();
    scheduler.current_task = (scheduler.current_task + 1) % scheduler.task_cnt;
  }
  m_uart.puts("OS: Back to OS\n");
}
```
簡直慘不忍睹……。

# 除錯小故事

故事並沒有到這裡就一帆風順，我把 code 改完之後，上線發現 uart 壞掉了…？
本來應該印出的字串全部印不出來，只有第一句 `rrxv6 start\n` 是正常的，初見覺得真的是超詭異，明明你們兩個一點關係都沒有為什麼會影響？

就用 gdb 追程式追了許久，都沒發現有問題，該 switch 的 task 都有 switch，進去 m_uart 的也都有進去，但就是沒有寫出東西。
後來注意到幾個現象：
1. debug code 會壞掉，但 release code 並沒有問題。
2. 試著把 main 的 code 砍掉一些，字串就多吐出來一部分，雖然有些是亂碼。

合著這兩點，想到之前在 debug 的時候，看到 rust debug code 吐出一堆缺乏最佳化的程式碼，猛然想到原因：
**竟然是 [stack overflow](https://stackoverflow.com/) 把要印的字串蓋過去**，uart 就印不出東西了。

這點用 objdump 得到證實：
```txt
riscv64-unknown-elf-objdump -d -j .bbs -j .rodata target/riscv64imac-unknown-none-elf/debug/rrxv6
0000000080003232 <.L__unnamed_4>:
    80003232: 6154 6b73 2031 7552 6e6e 6e69 0a67 7273     Task1 Running.sr
    80003242: 2f63 6373 6568 7564 656c 2e72 7372          c/scheduler.rs

0000000080003318 <STACK0>:
```

OS process 用的 STACK0 是在 0x80003318 ，我們會把 sp 設到 STACK0+4096，
但如果 stack 用太多，stack 就會一路從低位址寫，最後蓋到 0x80003232 儲存固定字串的地方。
用 gdb 也可以證實 stack overflow：
```txt
(gdb) watch $sp < 0x80003318
(gdb) c
Watchpoint 2: $sp < 0x80003318

Old value = false
New value = true

(gdb) bt
#0  rrxv6::scheduler::{{impl}}::default () at src/scheduler.rs:26
#1  0x000000008000152c in rrxv6::{{impl}}::deref::__static_ref_initialize () at src/main.rs:27
#2  core::ops::function::FnOnce::call_once<fn() -> spin::mutex::Mutex<rrxv6::scheduler::Scheduler, spin::relax::Spin>,()> ()
    at /rustc/16e18395ce33ca1ebfe60a591fb2f9317a75d822/library/core/src/ops/function.rs:227
#3  0x00000000800022ec in spin::once::Once<spin::mutex::Mutex<rrxv6::scheduler::Scheduler, spin::relax::Spin>>::call_once<spin::mutex::Mutex<rrxv6::scheduler::Scheduler, spin::relax::Spin>,fn() -> spin::mutex::Mutex<rrxv6::scheduler::Scheduler, spin::relax::Spin>> (
    self=0x8000bc00 <<rrxv6::SCHEDULER as core::ops::deref::Deref>::deref::__stability::LAZY>, builder=0x80002166 <core::slice::{{impl}}::iter<u8>+16>)
    at /home/yodalee/.cargo/registry/src/github.com-1ecc6299db9ec823/spin-0.5.2/src/once.rs:110
#4  0x00000000800005dc in lazy_static::lazy::Lazy<spin::mutex::Mutex<rrxv6::scheduler::Scheduler, spin::relax::Spin>>::get<spin::mutex::Mutex<rrxv6::scheduler::Scheduler, spin::relax::Spin>,fn() -> spin::mutex::Mutex<rrxv6::scheduler::Scheduler, spin::relax::Spin>> (
    self=0x8000bc00 <<rrxv6::SCHEDULER as core::ops::deref::Deref>::deref::__stability::LAZY>, builder=<optimized out>)
    at /home/yodalee/.cargo/registry/src/github.com-1ecc6299db9ec823/lazy_static-1.4.0/src/core_lazy.rs:21
#5  rrxv6::{{impl}}::deref::__stability () at /home/yodalee/.cargo/registry/src/github.com-1ecc6299db9ec823/lazy_static-1.4.0/src/lib.rs:142
#6  rrxv6::{{impl}}::deref (self=0x80003208 <.L__unnamed_1>)
    at /home/yodalee/.cargo/registry/src/github.com-1ecc6299db9ec823/lazy_static-1.4.0/src/lib.rs:144
#7  0x0000000080000af0 in rrxv6::scheduler::task_create (f=0x8000094a <rrxv6::proc::user_task0>) at src/scheduler.rs:40
#8  0x0000000080000a26 in rrxv6::proc::user_init () at src/proc.rs:35
#9  0x000000008000039a in rrxv6::main () at src/main.rs:36
```

答案就在這裡：lazy_static 在你第一次使用到 lazy 物件時，會先呼叫你在 lazy_static 寫的函式 default 來初始化 static 變數，
而這個初始化函式當然也會佔用 stack，當我們 Scheduler 的尺寸很大的時候，OS 就會一路寫出去寫到不亦樂乎。  
而 release code 因為 rust 用了更多最佳化，stack 用得少就(暫時)沒有 overflow 的問題了。

因為這樣，我把 Scheduler 的 stack_task 搬出去變成 static，反正 rust code 沒有要真的寫入它，只是把 sp register code 設過去而已，後面的讀寫都不是我的錯（欸。  
但就算經過瘦身，debug code 還要把 STACK0 加大到 8192 bytes 才夠使用，究竟 rust debug code 是做了什麼用這麼多的 stack 呢…？  
對這個問題我是滿好奇的，如果 os process 用太多 stack 沒人擋得住它，這顯然是個問題，一般的 OS 開發又是怎麼樣檢測或阻止這樣子的問題呢？  

長期的解決方案還是要把 stack 跟 context 的變成動態宣告，這就要等我們進行到記憶體管理才能處理了。
