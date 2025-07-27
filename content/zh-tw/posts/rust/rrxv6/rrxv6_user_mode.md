---
title: "rrxv6 : user mode"
date: 2022-05-23
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
- /images/rrxv6/usermode.png
forkme: rrxv6
---

上一回我們實作完 scheduler 之後，下一個大項目就是進入 user space 以及 system call 了，

有了這篇一般使用者和作業系統才能真的分隔開來，使用者行程在獨立的空間，以受限的權限運作，作業系統則從外管理使用者行程。
<!--more-->

# Init User Process

上一章實作的 process，包括幾個資料：state、context、kstack、pid、name。  
新加上的 TrapFrame 和 PageTable，分別代表進到 user space 還需要的兩個東西，一個是管好記憶體，另一個則是管好 Trap：
```rust
use core::ptr::NonNull;

pub struct Proc {
  pub state: ProcState,
  pub context: Context,
  pub kstack: u64,
  pub pid: usize,
  pub memory_size: u64,
  pub name: [u8;LEN_PROCNAME],
  pub trapframe: NonNull<TrapFrame>,
  pub pagetable: NonNull<PageTable>,
}
```

先前我們是呼叫 scheduler 的 spawn 函式，把 process 塞進 scheduler 的 used_list 裡；以下是新的函式 init_userproc:
```rust
/// initialize first user process
pub fn init_userproc() {
  let scheduler = get_scheduler();
  let mut proc = scheduler.unused.pop()
      .expect("init_userproc failed");

  match alloc_process(&mut proc) {
    Err(_s) => {
      proc.reset(true);
      panic!("init_userproc: alloc_process");
    }
    Ok(()) => {
      // initialize user pid
      proc.pid = get_pid();

      // initialize memory map
      unsafe {
        let pagetable = proc.pagetable.as_mut();
        init_uvm(pagetable, &INITCODE);
      }
      proc.memory_size = PAGESIZE;

      // Note that first user process will have its pid 0
      // we don't save additional pointer to this process
      assert!(proc.pid == 0, "User process init pid != 0");

      // initialize trapframe
      unsafe {
        let trapframe = proc.trapframe.as_mut();
        trapframe.epc = 0;
        trapframe.sp = PAGESIZE;
      }

      // set process name
      proc.set_name("initcode");

      // set state to RUNNABLE
      proc.state = ProcState::RUNNABLE;

      let mut used_list = scheduler.used.lock();
      used_list.push(proc);
    },
  }
}
```

主體和 spawn 是一樣的，同樣是從 unused_list 拿出一個 process，設定完，塞回 used_list 裡面。  
中間一步步包括：
1. alloc_process 分配記憶體給 trapframe, pagetable
2. 將程式碼複製進 pagetable
3. 設定 trapframe 到初始位置，stack pointer = 4096 及執行位址 epc 0x0
4. 其他如設定 pid, name, state 等等，在上一章已經有看過了

以下就來一步步拆解這個函式的實作。

## PageTable

先從 PageTable 開始，為什麼這裡不能用直接帶一個 `pagetable: PageTable` 呢？  
因為我們需要 PageTable 指向一塊特別 allocate 的 4KB 的記憶體，需要用 pointer 處理。

這裡我們使用 [core::ptr::NonNull](https://doc.rust-lang.org/std/ptr/struct.NonNull.html)，
是一種…比 raw pointer 多一點封裝的型別，NonNull 保證 pointer 的內容絕對不會是 0 (NULL)，但仍然可以是 dangling，
使用它還是會爆掉；介紹文件上提了看似跟計算理論有點關係的 unsoundness, covariat 之類的，我也看不太懂。  

在初始化的時候，可以使用 NonNull::dangling 進行初始化，我在 gdb 檢查的時候發現 pointer 內容初始化為 0x4，
覺得這根本沒屁用，還不是指向垃圾位址，脫褲子放屁的感覺：
```rust
pub fn new(kstack: u64) -> Self {
  Self {
    state: ProcState::RUNNABLE,
    context: Context::new(),
    kstack,
    pid: 0,
    memory_size: 0,
    name: [0;LEN_PROCNAME],
    trapframe: NonNull::dangling(),
    pagetable: NonNull::dangling(),
  }
}
```

這個 PageTable 會在 user process 將要執行的時候，替換掉目前使用的 page table，
如此一來 CPU 看到的記憶體空間就會轉變成 user space。  

下面簡單畫一下 xv6 設計上 kernel space 和 user space 上各看到什麼：

### kernel pagetable

kernel space 看到的比較複雜一點，除了要映射 kernel code 以及硬體元件的存取之外。
還要映射整塊 memory allocation 的區域、kernel stack (kstack) 指向分配出來的記憶體、trampoline 指向 kernel code 後接的 trampoline 區域。

![kernelmap](/images/rrxv6/kernelmap.jpg)

### user pagetable

user space 就簡單多了，trapframe 和 user code 是從 memory allocation 分配出來的 page，映射在 0 和 0x7FFFFFE000；
trampoline 和 kernel 的 trampoline 一樣，映射到實體記憶體的 trampoline 位置。

![usermap](/images/rrxv6/usermap.jpg)

稱為 trampoline - 彈跳床 - 的 assembly 是 user space 和 kernel space 間溝通的橋樑，兩邊都會將虛擬位址 0x7FFFFFF000 的一個分頁指向 trampoline 的位址，
因此無論 user space 或 kernel space 都能存取其中的兩個函式：`uservec` 和 `userret`。  
`uservec` 處理 User Mode 下接到的中斷，從 User Mode 進入 Supervisor Mode；`userret` 則是從 Supervisor Mode 進入 User Mode。

## TrapFrame

TrapFrame 是做什麼用的呢，可以參考[予焦啦！scratch 控制暫存器
](https://ithelp.ithome.com.tw/articles/10273704?sc=rss.iron)。

程式執行到一半，如果硬體天外飛來一筆中斷，這時就必須暫停使用者行程，進到中斷處理程序去處理中斷，
因此我們會需要一個額外的空間保存當下行程的內容（暫存器），也就是 TrapFrame。

以下是 TrapFrame 的內容，包括 5 個與 kernel 相關的 register，剩餘則是要保存的 user process 的 register。
```rust
#[repr(C)]
#[derive(Debug,Default,Clone,Copy)]
pub struct TrapFrame {
  pub kernel_satp: Reg,   //   0 kernel page table
  pub kernel_sp: Reg,     //   8 top of process's kernel stack
  pub kernel_trap: Reg,   //  16 usertrap()
  pub epc: Reg,           //  24 saved user program counter
  pub kernel_hartid: Reg, //  32 saved kernel tp
  pub ra: Reg,            //  40
  pub sp: Reg,            //  48
  pub gp: Reg,            //  56
  pub tp: Reg,            //  64
  pub t0: Reg,            //  72
  pub t1: Reg,            //  80
  pub t2: Reg,            //  88
  pub s0: Reg,            //  96
  pub s1: Reg,            // 104
  pub a0: Reg,            // 112
  pub a1: Reg,            // 120
  pub a2: Reg,            // 128
  pub a3: Reg,            // 136
  pub a4: Reg,            // 144
  pub a5: Reg,            // 152
  pub a6: Reg,            // 160
  pub a7: Reg,            // 168
  pub s2: Reg,            // 176
  pub s3: Reg,            // 184
  pub s4: Reg,            // 192
  pub s5: Reg,            // 200
  pub s6: Reg,            // 208
  pub s7: Reg,            // 216
  pub s8: Reg,            // 224
  pub s9: Reg,            // 232
  pub s10: Reg,           // 240
  pub s11: Reg,           // 248
  pub t3: Reg,            // 256
  pub t4: Reg,            // 264
  pub t5: Reg,            // 272
  pub t6: Reg,            // 280
}
```

uservec 是 user mode 下中斷的處理函式，它會從 trapframe 中取出 kernel 相關的資訊，然後跳入 supervisor mode 進行處理，
不用急，我們在下一章 syscall 的時候就會好好解釋它在幹嘛。

從 trapframe 的角度來看，一個 process 執行會需要儲存三套 CPU 執行的資訊（也就是暫存器的記錄），
執行的時候三套有一套會位在 CPU 上執行，其他則存於 proc 的結構當中：
1. user process：現正執行的 process。
2. scheduler：存在 proc.context 內，在 context switch 時交換到 CPU 上。
3. trap handler：存在 proc.trapframe 內，在 trap handler 時交換到 CPU 上。

## allocate process

因為加上了新的 trapframe 和 pagetable，在 spawn process 要加上新的 alloc_process 以及呼叫的 init_user_pagetable：

```rust
fn alloc_process(proc: &mut Proc) -> Result<(), &str> {
  // allocate memory for trapframe
  proc.trapframe = NonNull::new(kalloc() as *mut _)
      .ok_or("kalloc failed in alloc user trapframe")?;

  // allocate memory for pagetable
  proc.pagetable = init_user_pagetable(&proc)
      .ok_or("kalloc failed in alloc user pagetable")?;

  // forkret will return to user space
  proc.context.reset();
  proc.context.ra = forkret as u64;
  proc.context.sp = proc.kstack + PAGESIZE;

  Ok(())
}
```
alloc_process 分配 trapframe 記憶體，以及呼叫 init_user_pagetable 分配 pagetable 的記憶體；
最後設定 context.sp 到初始狀態，context.ra 設定為 forkret 函式。

```rust
pub fn init_user_pagetable(proc: &Proc) -> Option<NonNull<PageTable>> {
  let mut page_table_ptr = NonNull::new(kalloc() as *mut _)?;
  let page_table = unsafe { page_table_ptr.as_mut() };

  // map the trampoline code (for system call return)
  // only the supervisor uses it, on the way to/from user space, so not PTE_U.
  let trampoline = PhysAddr::new(trampoline as u64);
  if let Err(_e) = map_pages(page_table, VirtAddr::new(TRAMPOLINE), trampoline, 
      PAGESIZE, PteFlag::PTE_READ | PteFlag::PTE_EXEC) {
    return None;
  };

  let trapframe = PhysAddr::new(proc.trapframe.as_ptr() as u64);
  if let Err(_e) = map_pages(page_table, VirtAddr::new(TRAPFRAME), trapframe, 
      PAGESIZE, PteFlag::PTE_READ | PteFlag::PTE_WRITE) {
    return None;
  };
  Some(page_table_ptr)
}
```

init_user_pagetable 負責分配 pagetable 的記憶體，並且映射 trampoline 和 trapframe 到對應的 virtual address，
這只需要呼叫在[virtual memory]({{<relref "rrxv6_virtual_memory#map_pages">}}) 所寫的 map_pages 即可。  
注意到我們在這兩個函式上大量應用 Result, Option 作為函式的回傳值，這樣就能大量用 rust question mark ? 語法，
比起 `match` 或 `if let` 語法都能大幅扁化排版的縮排。

## initcode

initcode 是我們 User space 最開始執行的程式，內容同樣是 assembly 寫就，
在 xv6 裡，它會由設定好參數呼叫 system call sys_exec 執行 /init 的內容。  
我們這裡還沒設定檔案系統，也還沒有 system call，那我們的 initcode 要做什麼呢？  
莫忘初衷，「作業系統的 Hello World」也就是一個無窮迴圈。

```asm
.globl start
start:
loop:
  j loop
```

這段 code 會放在另一個資料夾 user 中，透過 riscv 工具鏈編譯成執行檔。
```shell
riscv64-unknown-elf-gcc -Wall -Werror -O -fno-omit-frame-pointer -ggdb -gdwarf-2 \
   -march=rv64g -nostdinc -I. -Ikernel -c user/initcode.S -o user/initcode.o
riscv64-unknown-elf-ld  -N -e start -Ttext 0 -o user/initcode.out user/initcode.o
riscv64-unknown-elf-objcopy -S -O binary user/initcode.out user/initcode
riscv64-unknown-elf-objdump -S user/initcode.o > user/initcode.asm
```

用 `od -t xC user/initcode` 或者是 `xxd -p user/initcode` 就能取得編譯完，真的要給 CPU 執行的程式內容：
```bash
$ od -t xC user/initcode
0000000 6f 00 00 00
0000004
```

把這段 code 放到 rust 並稍加改裝：
```rust
/// The first user program that run infinite loop
/// od -An -t x1 initcode
pub static INITCODE: [u8;4] = [
  0x6f,0x00,0x00,0x00
];
```

函式 init_uvm 用來初始化程式，我們會分配一個 page 的記憶體給 uvm，並呼叫 map_pages 將它對應到 Virtual Address = 0 的位址上，
Flag 設定為 RWXU；再將外面提供的 code - 也就是 INITCODE 的程式碼複製到記憶體。
```rust
pub fn init_uvm(page_table: &mut PageTable, code: &[u8]) {
  let size = code.len();
  let pagesize = PAGESIZE as usize;
  if size > pagesize {
      panic!("init_uvm: more than a page");
  }
  let ptr = kalloc();
  unsafe {
      write_bytes(ptr, 0, pagesize);
      let va = VirtAddr::new(0);
      let pa = PhysAddr::new(ptr as u64);
      let perm = PteFlag::PTE_READ | PteFlag::PTE_WRITE | PteFlag::PTE_EXEC | PteFlag::PTE_USER;
      map_pages(page_table, va, pa, PAGESIZE, perm)
          .expect("init_uvm");
      copy::<u8>(code.as_ptr() as *const u8, ptr, size);
  }
}
```

# User Trap Return

在 scheduler 將 process context 換入之後，處理器會從 forkret 函式執行，forkret 會立即呼叫 usertrapret 這個函式。

```rust
pub fn forkret() {
    unsafe {
        usertrapret();
    }
}
```

usertrapret 是這次實作的重中之重，它會完成從 kernel space 進到 user space 的所有程序：
1. 關閉*supervisor* 的 interrupt（reset csr sstatus 的 SIE big），interrupt 由 User Mode 承接。
2. 設定 stvec 指向 uservec，處理器在 interrupt 的時跳到 uservec 執行
3. 設定 trapframe kernel 相關的部分：
    1. 現在 csr satp 的值寫入 trapframe.kernel_satp
    2. kernel stack pointer 存入 kernel_sp
    3. usertrap 的位址寫入 kernel_trap，在 uservec 裡會呼叫 kernel_trap 也就是 usertrap 處理 trap。
    4. 現在的 hartid 寫入 kernel_hartid
4. 設定 sstatus
    1. 設定 SPP 為 UserMode，表示我在進到現在這個 Supervisor Mode 之前是來自於 User Mode，呼叫 sret 指令的時候就會切換模式為 User Mode
    2. 設定 SPIE 讓 User Mode 承接 interrupt。
5. 對 sepc 寫入 trapframe.epc，epc 的內容未來會是 user space process 執行時 program counter 的值。
6. 從 process 的 pagetable 取出 user pagetable 的位址，這是第二個參數 $a1。
7. TRAPFRAME 做為第一個參數 $a0，呼叫 userret 準備進入 user mode。

```rust
pub unsafe fn usertrapret() {
  let proc = get_proc() as *mut Box<Proc>;

  // 1. disable supervisor interrupt
  intr_off();

  // 2. stvec to uservec
  let mut stvec = Stvec::from_bits(0);
  stvec.set_addr(TRAMPOLINE + (uservec as u64 - trampoline as u64));
  stvec.write();

  // 3. set up trapframe values that uservec will need when
  let trapframe = (*proc).trapframe.as_mut();
  let satp = Satp::from_read();
  trapframe.kernel_satp = satp.bits();           // kernel page table
  trapframe.kernel_sp = (*proc).kstack + PAGESIZE; // process's kernel stack
  trapframe.kernel_trap = usertrap as u64;
  trapframe.kernel_hartid = tp::read();          // hartid for cpuid()

  // 4. set csr sstatus SPP and SPIE
  let mut sstatus = Sstatus::from_read();
  sstatus.set_spp(Mode::UserMode); // clear SPP to 0 for user mode
  sstatus.set_spie(true);
  sstatus.write();

  // 5. set SEPC to the saved user pc.
  Sepc::from_bits(trapframe.epc).write();

  // 6. prepare $a1
  let mut satp = Satp::from_bits(0);
  let pagetable = (*proc).pagetable.as_mut();
  satp.set_mode(SatpMode::ModeSv39);
  satp.set_addr(pagetable as *const _ as u64);
  let satp = satp.bits();

  // 7. call userret, enter user mode
  let fp = (TRAMPOLINE + (userret as u64 - trampoline as u64)) as *const ();
  let code: fn(u64, u64) = core::mem::transmute(fp);
  code(TRAPFRAME, satp)
}
```

## usertrap

如同 kernelvec -> kerneltrap；User Mode 也有對應的 uservec -> usertrap 函式。
我們的實作先留個無窮迴圈在裡面，下一章 syscall 的時候再實作：
```rust
/// handle an interrupt, exception, or system call from user space.
/// called from trampoline.S, must not mangle its name
#[no_mangle]
pub fn usertrap() {
  loop {}
}
```

# userret
終於來到最後一步 userret 了，這段位在 trampoline 區段，assembly 實作的 code。

```asm
.globl userret
userret:
  # userret(TRAPFRAME, pagetable)
  # switch from kernel to user.
  # usertrapret() calls here.
  # a0: TRAPFRAME, in user page table.
  # a1: user page table, for satp.

  # switch to the user page table.
  csrw satp, a1
  sfence.vma zero, zero
```

第一步是把放在參數 $a1 裡面的 satp 值寫入 satp 裡面，並呼叫 sfence.vma 清空 TLB。  
為什麼要**進到 userret 之後**才覆寫 satp？  
這是因為 usertrapret 還是 kernel code，它在 user process 的 pagetable 裡面並沒有映射，在 usertrapret 就換掉 satp 會直接跳 memory access fault。  
進到 userret 之後就是在 trampoline 內，kernel/user pagetable 都有對應，程式才能正常執行。

我在 debug 的時候也遇過 break point 打在 usertrapret，sfence.vma 一下去 gdb 就跳錯誤，但明明我 pagetable 都沒設錯。  
後來發現是 break point 還在 kernel code 的位址，gdb 沒辦法印出 break point 的資訊就一直報錯，把 break point 移除就沒問題了。

```asm
  ld t0, 112(a0)
  csrw sscratch, t0

  # restore all but a0 from TRAPFRAME
  ld ra, 40(a0)
  ld sp, 48(a0)
  ld gp, 56(a0)
  ld tp, 64(a0)
  ld t0, 72(a0)
  ld t1, 80(a0)
  ld t2, 88(a0)
  ld s0, 96(a0)
  ld s1, 104(a0)
  ld a1, 120(a0)
  ld a2, 128(a0)
  ld a3, 136(a0)
  ld a4, 144(a0)
  ld a5, 152(a0)
  ld a6, 160(a0)
  ld a7, 168(a0)
  ld s2, 176(a0)
  ld s3, 184(a0)
  ld s4, 192(a0)
  ld s5, 200(a0)
  ld s6, 208(a0)
  ld s7, 216(a0)
  ld s8, 224(a0)
  ld s9, 232(a0)
  ld s10, 240(a0)
  ld s11, 248(a0)
  ld t3, 256(a0)
  ld t4, 264(a0)
  ld t5, 272(a0)
  ld t6, 280(a0)

  # restore user a0, and save TRAPFRAME in sscratch
  csrrw a0, sscratch, a0

  # return to user mode and user pc.
  sret
```

這段利用了 [csr sscratch](https://five-embeddev.com/riscv-isa-manual/latest/supervisor.html#supervisor-scratch-register-sscratch)；它會

1. 先把 trapframe 的 $a0 值（112(a0)）透過 t0 寫入 sscratch 中保存。
2. 從 trapframe 裡將各種暫存器的值復原。
3. 用 csrrw 將 sscratch 中保存的 $a0 值與實際的 a0 register 交換內容。
4. sret 從 supervisor mode 結束，進入 user mode。

如此一來 sscratch 就變成本來的 $a0 ，也就是 process trapframe 的位址；所有本來在 trapframe 內的暫存器值也回到實體的暫存器內了。

可能有人疑惑，欸不是我們都沒動過 trapframe 的內容呀？  
沒錯，我們只有在[最開始]({{< relref  "#init-user-process" >}}) 有下面這段 code；

```rust
unsafe {
  let trapframe = proc.trapframe.as_mut();
  trapframe.epc = 0;
  trapframe.sp = PAGESIZE;
}
```

但這是沒問題的，從 Supervisor Mode 進入 User Mode，如同從 Machine Mode 進入 Supervisor Mode，是呼叫 sret/mret 像是從一個 trap 中 return。  

如果是正常的 trap，會有如下的程序：
1. 中斷發生，處理器寫入 csr mepc/sepc = PC + 4
2. 處理異常
3. 呼叫 mret/sret，PC = Mepc/Sepc。
從 Machine Mode 返回的話，會從 csr mepc 取出 trap 前執行的位址；Supervisor Mode 返回則是從 csr sepc。  
我們就像沒有中斷直接從 2 開始，設定好 mepc/sepc 呼叫 mret/sret 就會跳去對應的地方繼續執行了。

trapframe.epc 稍後會放入 sepc 中，sret 後 user process 就是從位址 0x0 開始，以 user mode 的權限開始執行；
stack pointer 則指向 PAGESIZE 4096 的位址。

# 測試

透過 gdb 可以看到，在 usertrapret 之後，執行數行 userret 的 assembly，前面的位址也變為 0 並不再離開，因為我們 user program 的確寫了無窮迴圈。

![usermode](/images/rrxv6/usermode.png)

另外如果我們設一個中斷在 usertrap 函式，持續執行則程式會陷入 usertrap 的無窮迴圈中。

![usertrap](/images/rrxv6/usertrap.png)

有件我不明白的事情是，為什麼 xv6 在除錯的時候，它都能正確顯示 userret 及 user program 內的 assembly code，我的 code 卻不行，真的很詭異。

# 總結

費了千辛萬苦我們的程式終於進到 user mode 了。  
可以看到，為了 User Mode 我們大部分的力氣，其實都花費在處理 pagetable 和 trapframe 上面，
特別是 trapframe，在下一章的 syscall，或者廣義的 trap 處理上會扮演重要的角色。
