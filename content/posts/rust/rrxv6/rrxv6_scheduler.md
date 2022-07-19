---
title: "rrxv6 : scheduler"
date: 2022-04-12
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
- /images/rrxv6/ABABAB.png
forkme: rrxv6
latex: true
---

上次我們發佈 rrxv6 的文章，已經是 2021 年 12 月的事情了，已經是去年了，大家可能以為我已經棄更了？  
其實沒有的，只是跟上次的 virtual memory 一樣卡關了。

1-2 月的時候，台北的天氣鳥得跟好市多的冷藏區一樣，冷就算了還天天下雨，起床之後在雨聲裡開工，中餐晚餐撐傘出去買飯，
在雨聲裡睡午覺，在雨聲裡說晚安，房間除溼開整天，到後來整個人都覺得不對勁了，還小病了一場一個星期捅了三次鼻孔；
二月俄烏又開戰~~幹普丁還我錢~~，有大事的時候真的會忍不住一直嘗試更新資訊，然後工作效率就降到低點QQ，
直到三月吸飽太陽能之後有好一點點。  
<!--more-->

# 參考資料

前情提要結束了，反正總之就是嚴重卡關。  

這次是卡哪裡呢，就是卡 process 跟 scheduler，和 memory management 和 ipc 並稱作業系統三大核心功能果然不簡單；
因為 Rust Mutex 的實作方式，如果照抄 xv6 的寫法，context switch 之後會直接 deadlock，還不是兩個 processes deadlock，
是 context switch 前後的同一個 process 自己 deadlock。

我遇到的問題就是**如何設計一個如同 xv6 用的 multicore 的 scheduler**，雖然…xv6 的實作不是很有效率，
可以 O(1) 的東西寫成 O(n)，而且不會 preempt（[preempt 的 scheduler 是作業](https://pdos.csail.mit.edu/6.828/2014/labs/lab4/)），
就是第一個 process 一直跑下去，

因此我訂的目標是，要寫一個 multicore 可用的 scheduler，至少要有 preempt 的功能，效率…不要太差；
期間看了不少其他的文章與 code 當參考，雖然沒有一個有真正解決到我的問題~~可以讓我直接抄作業~~，以下條列：
* [Blog os cooperative multitasking](https://os.phil-opp.com/async-await/)：用 rust 本身支援的語言特性 async/await 來實作協作式多工，這篇很精彩，但對我來說沒什麼用就是。
* [FreeRTOS scheduler](https://github.com/FreeRTOS/FreeRTOS-Kernel)：作為參考，C 語言的實作也看一下，但因為它沒有虛擬記憶體，所以對我的幫助也有限。
* [Tock os scheduler](https://github.com/tock/tock/tree/master/kernel/src/scheduler)：這是完成度最高的，內部結構錯綜複雜，trace 了好一陣才稍稍看懂。
它很帥氣的把 scheduler 弄成一個 trait，不同的 schedule policy 只是 trait 不同的實作，本篇使用 Linked List 也是學這邊的。

# xv6 rust 實作的問題
讓我們先試著重現 xv6 的 scheduler 函式：

```c
void scheduler(void)
{
  struct proc *p;
  struct cpu *c = mycpu();
  int found_running_process = 0;

  c->proc = 0;
  for(;;) {
    intr_on();

    found_running_process = 0;
    for(p = proc; p < &proc[NPROC]; p++) {
      acquire(&p->lock);
      if(p->state == RUNNABLE) {
        found_running_process = 1;

        p->state = RUNNING;
        c->proc = p;
        swtch(&c->context, &p->context);
        c->proc = 0;
      }
      release(&p->lock);
    }
    if (found_running_process == 0) {
      intr_on();
      asm volatile("wfi");
    }
  }
}
```

簡單來說，它所有可以跑的 process 都放在 `proc[NPROC]` 裡面，CPU 會一個一個 process 進去看，
如果找到狀態為 RUNNABLE 的 proc，就設定一下狀態然後拿出來跑，因為同時會有多個 CPU 執行這個函式，proc 會透過 Mutex lock 起來。

但問題就在這個 Mutex，如果我照抄的話，儲存行程的型態就會變成 `[Mutex<Proc>]`，直接改寫會類似：
```rust
for i in 0..NPROC {
  mut proc = PROC[i].lock();
  if proc.state == ProcState::RUNNABLE {
    found_process = true;

    proc.state = ProcState::RUNNING;
    *cpu.proc.lock() = Some(i);
    unsafe {
      switch(&cpu.context as *const Context,
             &proc.context as *const Context);
    }
  }
```

把 proc 的 index 存在 cpu 裡面，這樣要回來的時候可以從 index 取得它在執行的 proc，再呼叫 switch 把執行狀態存回去。  
問題在於：
```rust
mut proc = PROC[i].lock();
```

這行，Mutex 已經被 scheduler 拿走了，switch 的時候並不會自動解鎖這個 Mutex，所以 process 執行完，
要 context switch 取得 PROC[i] 的 Mutex 時就會直接 deadlock。  

具體可以用下面這張圖解釋：
![deadlock](/images/rrxv6/deadlock.png)

# 可行的實作

誠實地說，我下面這個實作也就只是 **可行** 而已，和能用的成品相去甚遠，大體來說就是會動~~有動六十分~~。
未來有高機率會需要改動設計。

這次的實作有三個要點：

1. scheduler 和 data struct 息息相關，要實作有效率的 scheduler，就得用上 list ，
而不是如 xv6 一樣用一個靜態的 array 來儲存所有的 process；雖然在 rust 上實作 list 相對來說麻煩一點，
但幸好這部分有 [Too Many Linked Lists](https://rust-unofficial.github.io/too-many-lists/fifth.html) 可以參考。
2. 跟[上次實作 Context]({{<relref "rrxv6_contextswitch">}}) 的時候一樣，我們需要用到 global data，
為了避免 context switch 前後互相競爭，這次 global data 就不能用 Mutex 了，存取也都會變成 unsafe，但……
我就 unsafe。
3. 同樣，為了持有一些資料的 reference，我們必須使用 pointer，這在 rust 裡也是 unsafe。

讓我們開始吧：

## Process

上一次我們用的是直接把函式的 context 準備好塞進 scheduler 裡，這回我們用 Process 把它包起來；
初始的 Process 先加上 state、context、stack address 跟 pid 即可：
```rust
#[derive(Eq,PartialEq)]
pub enum ProcState {
  RUNNABLE,
  RUNNING,
}

pub struct Proc {
  pub state: ProcState,
  pub context: Context,
  pub kstack: u64,
  pub pid: usize,
  pub name: [char;LEN_PROCNAME],
}
```

## process stack

xv6 會生成多個 kernel process，可以透過設定檔的 NPROC 來設定，在 kernel 初始化的時候會先分配好它們需要的記憶體；
xv6 的設計是分配在 virtual address 頂部的地方：

```
pub fn kstack(proc_id: u64) -> u64 {
  TRAMPOLINE - (proc_id + 1) * 2 * riscv::PAGESIZE
}
```

在[初始化 virtual memory]({{<relref "rrxv6_virtual_memory">}}) 的時候，要分配好實體記憶體並做好映射：
```rust
// alloc and map stack for kernel process
for i in 0u64..NPROC as u64 {
  let ptr = kalloc();
  if ptr == 0 as *mut u8 {
    panic!("kalloc failed in alloc proc stack");
  }
  let pa = PhysAddr::new(ptr as *const _ as u64);
  let va = VirtAddr::new(kstack(i));
  kvmmap(va, pa, PAGESIZE, PteFlag::PTE_READ | PteFlag::PTE_WRITE);
}
```

## scheduler

### tock os 的實作
scheduler 的部分主要是參考 tock os 的設計，雖然沒那麼簡潔，但還是儘量預留未來改為 trait 並允許不同實作的空間：

tock os 的 scheduler 只有五個介面函式：

1. next：請 scheduler 決定下一個要執行的 process。
2. result：通知 scheduler 上一個函式結束執行的原因。

後面這三個比較不重要，一般都是沿用標準的實作：

3. do_kernel_work_now：詢問 scheduler 是否要中斷 user process 以執行 kernel task。
4. continue_process：詢問 scheduler 是否要繼續執行同一個 process。
5. execute_kernel_work：要求 scheduler 排程執行 kernel-level work，像是處理 bottom-half interrupt；
特殊的 scheduler 可能會優先執行 task 以符合時間的需求。

至於一個 scheduler 的實作裡面要怎麼管理 process 那是它家的事，總之這幾個介面設定好就好。  
tock os 的 process 是在 kernel 裡儲存一個 static 的 process array；scheduler 則擁有這個 array 的 reference，
scheduler 會透過 process id 來指定要跑哪個 process 。

### 我的實作

我們仿造它的實作，先弄出一個 scheduler 的 struct，但我們把 process 都塞進 scheduler 裡面由 scheduler 來管，稍微簡單一點。  
先設立好 scheduler global variable 的空間，這一套應該是標準做法了

```rust
static mut SCHEDULER: Option<Scheduler> = None;

pub struct Scheduler {
  pub used: Mutex<List<Box<Proc>>>,
  pub unused: List<Box<Proc>>
}

pub fn get_scheduler() -> &'static mut Scheduler {
  unsafe {
    SCHEDULER.as_mut().unwrap()
  }
}

pub fn init_scheduler() {
  unsafe {
    SCHEDULER = Some(Scheduler::new());
  }
}
```

現在可以實作函式 `init_proc` 了，生成 NPROC 個 Proc，kstack 設定為先前映射好的 virtual address，
最後把它塞進 scheduler 的 unused list 裡。
```rust
pub fn init_proc() {
  let scheduler = get_scheduler();
  for i in 0..NPROC {
    let mut proc = Box::new(Proc::new(
      kstack(i as u64)
    ));
    scheduler.unused.push(proc)
  }
}
```

## spawn

初始化行程設計為 scheduler 的一個函式，比起 tock os scheduler 這是多出來的；具體包含：

1. 從 unused list 中取得一個 process 物件
2. 向 Atomic 的 static variable 取得 pid
3. 設定 state 為 RUNNABLE
4. 重設 context 之後，設定 stack pointer sp 為 kstack + PAGESIZE（riscv 的 stack 是 grow downward）；
return address 為 spawn 傳進來的函式位址 f。
5. 將設定好的函式插入 scheduler 的 used list 中。

```rust
pub fn get_pid() -> usize {
  static PID_GENERATOR: AtomicUsize = AtomicUsize::new(0);
  PID_GENERATOR.fetch_add(1, Ordering::Relaxed)
}

pub fn spawn(&mut self, f: u64) {
  match self.unused.pop() {
    Some(mut proc) => {
      // initialize process
      proc.pid = get_pid();
      proc.state = ProcState::RUNNABLE;
      proc.context.reset();
      proc.context.ra = f;
      proc.context.sp = proc.kstack + PAGESIZE;

      let mut used_list = self.used.lock();
      used_list.push(proc);
    },
    None => {
      panic!("No unused process left");
    }
  }
}
```

有了 spawn 函式，在 main 裡面我們就能把剛剛的東西都加進去，我們 spawn 兩個 printA 跟 printB 函式，分別印出 A 跟 B：
```rust
let scheduler = get_scheduler();
scheduler.spawn(print_a as u64);
scheduler.spawn(print_b as u64);
// start scheduling, this function shall not return
scheduler.schedule();

fn print_a() {
  loop {
    println("A");
  }
}

fn print_b() {
  loop {
    println("B");
  }
}
```

## static CPU

作業系統在執行的時候，從 CPU 的角度來看是這樣子的：
1. 執行到 scheduler，選出下一個要執行的 process，包括它所有的 registers 即 context。
2. 將 CPU 上現有的狀態存入記憶體的*某個地方*。
3. 從要執行的 process 狀態，載入到 CPU 上；2-3 步就是所謂的 context switch。
4. 這時候 CPU 會**立即** 開始執行 process，記住 CPU 是一刻都不會停的，register 指到哪就跑哪裡。
5. 無論是 process 自行放棄或是因為 interrupt，2-3 的步驟會反過來執行一次，CPU 即回到 scheduler 上。

為了儲存 Process 的狀態，上面的 Proc struct 裡面會有對應的 Context；
而在執行 process 時，每個 CPU 都會有一個空間去放原有的狀態，這就是我們拋棄節操的地方了。  
在 CPU 要從 Process 回到 kernel scheduler 時，它需要把現在的狀態，存回到 Proc struct 裡面，
這表示 CPU 必須持有執行中 Proc 的 mutable reference，為此我們需要使用 rust 的禁忌招式：pointer。

```rust
pub struct Cpu {
  pub proc: * mut Box<Proc>, // pointer to process running on this cpu
  pub context: Context,
}

static mut CPU: [Option<Cpu>;NCPU] = {
  const INIT_CPU: Option<Cpu> = None;
  [INIT_CPU;NCPU]
};

pub fn init_cpu() {
  for i in 0..NCPU {
    unsafe {
      CPU[i] = Some(Cpu::new());
    }
  }
}
```

## Context Switch

現在我們可以來實作 Context switch 了，跟之前[簡略的實作]({{<relref "rrxv6_contextswitch">}}) 沒差很多，

實作 next 介面，從 used list 裡面敲出下一個要執行的 process，由於 scheduler 會在多個 CPU 之間共享，
要修改 used_list 的時候，必須要搭配 Mutex lock，取出 Proc 之後立即解鎖，這樣它就不會卡到其他 CPU 的執行：

```rust
pub fn next(&self) -> Option<Box<Proc>> {
  let mut used_list = self.used.lock();
  used_list.pop()
}
```

上面用到的 schedule 函式：
1. 把 interrupt 打開
2. 呼叫 next 看看有沒有要執行的 process，沒有就直接進入休眠。
3. 拿到要執行的 process，設定它的狀態為 RUNNING，將 pointer 寫入 CPU struct。
4. 呼叫 assembly 的 [switch]({{<relref "rrxv6_contextswitch#assembly-context-switch">}})
執行 context switch。
5. 當 CPU 回到這裡（在 preempt 或 process 主動放棄執行），把這個 process 塞回 used list 裡，等待下一次被執行。

```rust
pub fn schedule(&self) -> ! {
  loop {
    intr_on();
    match self.next() {
      Some(mut proc) => {
        let cpu = get_cpu();
        proc.state = ProcState::RUNNING;
        unsafe {
          cpu.proc = &mut proc as *mut Box<Proc>;
          switch(&mut cpu.context as *mut Context,
                 &mut proc.context as *mut Context);
        }
        let mut used_list = self.used.lock();
        used_list.push(proc);
      },
      None => {
        intr_on();
        wfi();
      }
    }
  }
}
```

另外我們必須實作 yield_proc 函式（不叫 yield 是因為它是 rust 的關鍵字），讓 Proc 可以主動放棄 CPU 執行權。  
yield_proc 會從 cpu 裡面拿到 process 的 pointer，將狀態改回 RUNNABLE，再呼叫 switch 與 cpu 內部自己的 context
（停在 scheduler 內呼叫 switch 時的狀態）交換。

```rust
pub fn yield_proc() {
  let cpu = get_cpu();
  unsafe {
    let mut proc = &mut *cpu.proc as &mut Box<Proc>;
    proc.state = ProcState::RUNNABLE;
    cpu.proc = null_mut();

    switch(&mut proc.context as *mut Context,
           &mut cpu.context as *mut Context);
  }
}
```

## Preempt Multitasking

到這裡我們的 scheduler 已經能做到 cooperative multitasking 了，只要在 print_a/b 裡面呼叫 yield_proc 即可。  
不過要改造成 preempt 也很簡單，我們在[上一章 interrupt]({{<relref "rrxv6_interrupt">}}) 已經處理好 interrupt，
搭配在 start 的時[設定好了 machine mode timer interrupt]({{<relref "rrxv6_embedded_rust">}})。

這一串 interrupt 及其處理流程整理如下：
1. init_timer 設定 qemu clint (Core local interruptor)，設定對應的 timer setting，讓外部 timer 發中斷給 riscv hart。
2. init_timer 設定 CSR mtvec (Machine Trap-Vector Base-Address Register)，指定 machine trap 的 handler。
3. init_timer 設定 CSR mstatus (Machine-mode status register) 及 mie (Machine-mode Interrupt Enable)，讓外部 interrupt 能產生中斷。
4. 在 timer trap handler，重新設置 timer 並呼叫 csrw 設定 sip (Supervisor Interrupt Pending) 的 SSIP (Supervisor Software Interrupt Pending) 位元。
```asm
# raise a supervisor software interrupt.
li a1, 2
csrw sip, a1
```
5. 在 start 函式裡已經[設定 sie (Supervisor Interrupt Enable) 開啟 Software Interrupt]({{<relref "rrxv6_embedded_rust#%E5%85%B6%E4%BB%96%E7%9A%84-register">}})。
6. 呼叫 intr_on 時設定 sstatus (Supervisor Status Register)，開啟 Supervisor mode interrupt。
7. interrupt 發生，從 stvec 取出 handler kernelvel，保存 register 至 stack 上。
8. 呼叫 rust 函式 kerneltrap。

在 kerneltrap，透過 scause 知道現下是哪個 interrupt 或 exception，若發生的是 Supervisor-mode Software Interrupt，
呼叫寫好的 yield_proc 即可。  

```rust
fn handle_software_interrupt() {
  if get_cpuid() == 0 {
    tick();
  }

  let mut sip = Sip::from_read();
  sip.clear_pending(1);
  sip.write();

  let proc = get_proc();
  unsafe {
    if !proc.is_null() && (*proc).state == ProcState::RUNNING {
      yield_proc();
    }
  }
}
```

之所以必須要檢查 proc pointer 是不是 null，是設計的關係。  
只要 machine-mode 曾經把 sip 設 pending，在 intr_on 打開 sstatus 的瞬間 timer interrupt 就會被觸發，
在上述 schedule 函式呼叫 switch 進行 context switch 之前就進到 interrupt handler，cpu.proc 就會指向 null pointer。  
與之相對的如 FreeRTOS 的 ARM CM3 設計，在函式 `prvStartFirstTask`，它會先設定好 process pointer 之後，
再使用 cpsie 打開 interrupt，因此在 interrupt handler 就完全不用檢查持有的 process 是否為有效。

# 測試

測試其實沒有很複雜，qemu 執行下去就會看到畫面上交錯印出 A 和 B。

![ABABAB](/images/rrxv6/ABABAB.png)

這不禁讓我回想起很久很久以前，那時候小弟還很菜剛學會用 Linux，從傳說中的強者我同學 AZ 大大那邊借了一本
[鳥哥的私房菜](https://linux.vbird.org/linux_basic/centos7/) 回來讀，
開頭[介紹 linux 歷史的地方](https://linux.vbird.org/linux_basic/centos7/0110whatislinux.php#torvalds_multi) 有如下敘述：

> 他寫了三個小程式，一個程式會持續輸出A、一個會持續輸出B，最後一個會將兩個程式進行切換。他將三個程式同時執行，
> 結果，他看到螢幕上很順利的一直出現ABABAB......他知道，他成功了！ ^_^

對啦我也成功了，卡關三個月才進展這樣一點點，啊不就好棒棒。

# 結論

卡關三個月，記得那時出去買飯，一直在想到底要怎麼寫，才能在 rust 裡面實作 preempt multitasking，花時間 trace tock os 的 code 什麼的。  
最後的結論就是別傻了，什麼不要 unsafe，不要 pointer，只是讓自己被編譯器幹到懷疑人生。  
我就用 pointer，我就 unsafe，畢竟寫 OS 本身就是一件危險的事，unsafe 是避不過的，也是 OS 把 unsafe 的事都做完了，我們才能無憂無慮安全的用電腦，不用擔心沒事把硬體搞爆。

這章實在比預想還要長一些，下一章預期要進入 User process 與 syscall 啦。
