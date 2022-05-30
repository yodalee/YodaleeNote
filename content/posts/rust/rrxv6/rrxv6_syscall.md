---
title: "rrxv6 : syscall"
date: 2022-05-29
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
- /images/rrxv6/syscall_helloworld.png
forkme: rrxv6
latex: true
---

上一回我們進入 User Mode，打鐵趁熱這回就來處理 User Mode 下的 interrupt ，
以及實作其中一種比較特殊的 interrupt，也就是 system call。

<!--more-->

先來看看 User Mode 下發生 trap 會發生什麼事。

首先，上一回在 [usertrapret]({{< relref "rrxv6_user_mode#user-trap-return" >}}) 裡，
我們會設定 stvec 的值為 uservec，trap 發生時處理器會跳入 Supervisor Mode，PC 指向 uservec 開始執行。
此時 page table 仍然是 User Mode 的 page table，只能看到 user program 和 trampoline。

```asm
.globl uservec
uservec:
  # swap a0 and sscratch
  csrrw a0, sscratch, a0

  # save the user registers in TRAPFRAME
  sd ra, 40(a0)
  sd sp, 48(a0)
  sd gp, 56(a0)
  sd tp, 64(a0)
  sd t0, 72(a0)
  sd t1, 80(a0)
  sd t2, 88(a0)
  sd s0, 96(a0)
  sd s1, 104(a0)
  sd a1, 120(a0)
  sd a2, 128(a0)
  sd a3, 136(a0)
  sd a4, 144(a0)
  sd a5, 152(a0)
  sd a6, 160(a0)
  sd a7, 168(a0)
  sd s2, 176(a0)
  sd s3, 184(a0)
  sd s4, 192(a0)
  sd s5, 200(a0)
  sd s6, 208(a0)
  sd s7, 216(a0)
  sd s8, 224(a0)
  sd s9, 232(a0)
  sd s10, 240(a0)
  sd s11, 248(a0)
  sd t3, 256(a0)
  sd t4, 264(a0)
  sd t5, 272(a0)
  sd t6, 280(a0)
  # save the user a0 in p->trapframe->a0
  csrr t0, sscratch
  sd t0, 112(a0)
```

這時候很重要的就是 csr sscratch 了，這是一個用來暫存的空間，在 user mode 的時候會指向 process 的 trapframe。  
為什麼我們需要暫存空間？因為所有 register 都記錄了 user process **當下**執行的狀態，**修改到任一個 register 都不行**，
一定要有額外的 csr 作為暫存。  
因此第一步先用 csrrw 將 sscratch 與 a0 交換，接著就可以拿著 a0，把現在 user program 的執行狀態全部塞進 trapframe 裡面；
再用空出手的 t0 把 sscratch 裡的 a0 值拿出來存進去。

```asm
  # restore kernel stack pointer from p->trapframe->kernel_sp
  ld sp, 8(a0)
  # make tp hold the current hartid, from p->trapframe->kernel_hartid
  ld tp, 32(a0)
  # load the address of usertrap(), p->trapframe->kernel_trap
  ld t0, 16(a0)
  # restore kernel page table from p->trapframe->kernel_satp
  ld t1, 0(a0)
  csrw satp, t1
  sfence.vma zero, zero

  # a0 is no longer valid, since the kernel page
  # table does not specially map p->tf.

  # jump to usertrap(), which does not return
  jr t0
```

接著開始復原 supervisor mode 的執行狀態，註解應該寫很清楚了
1. 把 kernel stack pointer
2. kernel hartid 復原（雖然我不知道 $tp hartid 這個 csr 是有多重要）
3. 復原 supervisor page table
4. 跳入 usertrap，注意[用的是 jr 而不是 jalr](https://hackmd.io/@0xff07/doxolinux/%2F%400xff07%2FrkXNt1PXD)，因為這一跳不需要回來的位址。

# User Trap

user trap 經過一番改造。

sstatus 在 trap 發生的時候會自動把當下的模式寫入 SPP 裡，所以檢查 SPP 應該是 User Mode；接下來是：

1. 因為我們已經在 Supervisor Mode 了，改寫 csr stvec，改為由 kernelvec 承接 interrupt。
2. 在 trap 發生的時候，處理器會將當下的 PC 寫入 csr sepc 中，這時要將這個值保存下來，存進 trapframe 的 epc 中。
3. 透過 scause 得知現在是哪一個 interrupt/exception，如果發生的是 EnvironmentCallUMode，表示是 User Mode ecall 指令引起的軟中斷，即會呼叫 syscall 函式處理。

同樣是上一章的 [usertrapret]({{< relref "rrxv6_user_mode#user-trap-return" >}})
我們知道 trapframe.epc 會被 usertrapret 寫回 sepc，在 sret 的時候拿出來放回 PC 中；
在 syscall 的時候我們會修正 epc，改為 epc+4 下一個指令，否則我們處理完 ecall 跳回去又再執行一次 ecall 就沒完沒了了。

同理，這個函式也會呼叫 usertrapret 返回 User Mode。

```rust
#[no_mangle]
pub fn usertrap() {
  let sstatus = Sstatus::from_read();
  if sstatus.get_spp() != Mode::UserMode {
    panic!("usertrap: not from user mode");
  }

  // send interrupts and exceptions to kerneltrap(),
  // since we're now in the kernel.
  Stvec::from_bits(kernelvec as u64).write();

  let proc: *mut Box<Proc> = get_proc();
  let trapframe = unsafe { (*proc).trapframe.as_mut() };

  // save user program counter.
  trapframe.epc = Sepc::from_read().bits();

  let scause = Scause::from_read();
  let code = scause.get_code();
  if scause.is_interrupt() {
    println("usertrap: unexpected scause");
    unimplemented!("uservec: unexpected interrupt");
  } else {
    match code {
      x if x == Exception::EnvironmentCallUMode as u64 =>  {
        // system call
        // TODO: check process is killed

        // sepc points to the ecall instruction,
        // but we want to return to the next instruction.
        trapframe.epc += 4;

        // an interrupt will change sstatus &c registers,
        // so don't enable until done with those registers.
        intr_on();

        syscall();
      }
      _ => {
        unimplemented!("uservec: unexpected exception");
      }
    }
  }

  unsafe {
    usertrapret();
  }
}
```

# Syscall

到這裡我們已經知道 Syscall 根本毫無神奇之處，就是一個軟中斷後呼叫的函式。  
以下定義了 SYSCALLS 這個靜態陣列，Rust 強制你要明確定義陣列的長度，不像 C 可以實作不定長度的陣列，
所以我目前只能這樣寫，還找不到更好的寫法。  
syscall 函式會從 $a7 裡拿到使用者想要呼叫的 syscall id；用 a7 似乎是慣例，a0-a5 是函式的參數，a6 則不使用。

```rust
const SYSCALL_NUM : usize = 1;
type SyscallEntry = fn() -> u64;
static SYSCALLS: [SyscallEntry;SYSCALL_NUM] = [
  syscall_write
];

pub fn syscall() {
  unsafe {
    let proc = get_proc();
    let trapframe = (*proc).trapframe.as_mut();
    let syscall_id : usize = trapframe.a7 as usize;

    trapframe.a0 = if syscall_id < SYSCALLS.len() {
      SYSCALLS[syscall_id]()
    } else {
      u64::MAX
    }
  }
}
```

# syscall write

這個 syscall 在 xv6 本來是要用來對檔案寫入的，但我們還沒有檔案系統，因此先寫個會印出字串的 syscall。  
syscall_write 會從 A0 取得字串長度，A1 取得字串內容並印出。

```rust
fn syscall_write() -> u64 {
  let len = get_arg(ArgIndex::A0);
  let mut buf = vec![0; len as usize];
  get_str(ArgIndex::A1, &mut buf);
  println!("{}", String::from_utf8_lossy(&buf));
  // FIXME the real write size
  len
}
```

`get_arg` 封裝從 trapframe 裡拿出 a0-a5 register，這個就沒什麼好講的了。

```rust
enum ArgIndex {
  A0, A1, A2, A3, A4, A5,
}

/// get u64 raw value store in trapframe->a0 to a5
fn get_arg(n: ArgIndex) -> u64 {
  let proc = get_proc();
  let trapframe = unsafe { (*proc).trapframe.as_mut() };
  match n {
    ArgIndex::A0 => trapframe.a0,
    ArgIndex::A1 => trapframe.a1,
    ArgIndex::A2 => trapframe.a2,
    ArgIndex::A3 => trapframe.a3,
    ArgIndex::A4 => trapframe.a4,
    ArgIndex::A5 => trapframe.a5,
  }
}
```

## get_str

get_str/copy_in_str 是相對比較複雜的東西，類似 Linux system call 實作中的 copy_from_user；
因為要印的字串是存在於 User Mode 下的 page table；Supervisor Mode 是無法存取的，所以會需要一個特別的處理。

kernel 會先從 $a1 拿到 pointer，對著 process 內存著的 user pagetable，把對應位址的資料複製進 buffer 中。
```rust
/// Fetch the nul-terminated string at addr from the current process.
/// Returns length of string, not including nul, or -1 for error.
fn get_str(n: ArgIndex, buf: &mut [u8]) -> u64 {
  let addr = get_arg(n);
  let proc = get_proc();
  let page_table = unsafe { (*proc).pagetable.as_mut() };
  match copy_in_str(page_table, addr, buf) {
    None => u64::MAX,
    Some(len) => len
  }
}
```

我在 copy_in_str 使用了[從 rust forum 問到的寫法](https://users.rust-lang.org/t/help-with-some-abstraction-on-my-tree-walking-code/75753)，
將尋找 pagetable 這件事虛擬化，果然 code 寫不出來就是上 forum，rust 社群真的樂於助人，昨天問今天就有結果。

這裡定義了 AddrMapper 並實作 trait PageTableVisitor；這個 trait 把尋找 page table 封裝成兩個不同的行為：
1. nonleaf 遇到非 leaf 的 page 該做什麼。
2. leaf 遇到 leaf page 該做什麼。

如此一來 AddrMapper 的行為就是：

```rust
struct AddrMapper;

impl PageTableVisitor for AddrMapper {
  type Output = Option<PhysAddr>;
  fn is_valid_va(&self, va: VirtAddr) -> bool {
    va < VirtAddr::new(MAXVA)
  }
  fn leaf(&self, pte: &PageTableEntry) -> Self::Output {
    let flag = pte.flag();
    if !flag.contains(PteFlag::PTE_VALID | PteFlag::PTE_USER) {
      return None
    }
    Some(PhysAddr::new(pte.addr()))
  }
  fn nonleaf(&self, pte: &PageTableEntry) -> Self::Output {
    let flag = pte.flag();
    if !flag.contains(PteFlag::PTE_VALID) {
      return None;
    }
    Some(PhysAddr::new(0))
  }
}

/// Look up a virtual address, return Option physical address,
/// Can only be used to look up user pages.
fn map_addr(page_table: &PageTable, va: VirtAddr) -> Option<PhysAddr> {
  let mapper = AddrMapper;
  PageTableWalker::new(
      page_table,
      va,
      PageTableLevel::Two,
      mapper
  ).and_then(|mut walker| walker.visit())
}
```

最後是 copy_in_str 的實作，透過 map_addr 拿到實體位址，就可以從對應的位址把資料複製出來了。  
這邊用 iterator 搭配 take_while, zip 等手法，再用 count 收攏，可以寫出風格和 C kernel 極為不同的實作，雖然比這個沒什麼意義啦。  
效能上從 release code 上我是看不出來會不會比自己手爆來得快就是。~~其實是 release code 根本看不出哪段對應這段~~。

```rust
pub fn copy_in_str(page_table: &mut PageTable, addr: u64, buf: &mut [u8]) -> Option<u64> {
  let max_len = buf.len();
  let base = align_down(addr, PAGESIZE);
  let offset = addr - base;
  let va = VirtAddr::new(base);
  let pa = map_addr(page_table, va)?;
  let n = cmp::min(max_len, (PAGESIZE - offset) as usize);

  let addr = (pa + offset).as_u64() as *const _;
  unsafe {
    let slice: &[u8] = from_raw_parts::<u8>(addr, n);
    let len = slice
      .iter()
      .take_while(|c| **c != 0)
      .zip(buf.iter_mut())
      .map(|(a, b)| *b = *a)
      .count();
    Some(len as u64)
  }
}
```

# User Program

上一章的 initcode 只有一個無窮迴圈，現在讓我們加上 system call 跟一個無窮迴圈。  
riscv 的 syscall 指令為 ecall (environment call)，會產生一個軟中斷；這裡的實作應該很好懂：
* a7 填入想要呼叫 system call 的代號
* a0 填入字串的長度
* a1 填入 "Hello World!" 的位址

```asm
.globl start
start:
  li a0, 13
  la a1, helloworld
  li a7, 0
  ecall
loop:
  j loop

.data
helloworld: .ascii "Hello World!"
```

# 測試

一樣開始 gdb ，並停在 syscall 上，可以看到 trapframe 內的 register，分別是 字串長度 13；字串位址 0x14；syscall id 0。
![syscall](/images/rrxv6/syscall.png)

使用 xxd 去看編譯出來的 initcode，也可以看到 Hello World 的確在偏移 0x14 的位址。

```txt
$ xxd initcode
00000000: 1305 d000 9305 4001 9308 0000 7300 0000  ......@.....s...
00000010: 6f00 0000 4865 6c6c 6f20 576f 726c 6421  o...Hello World!
```

最後是 kernel 視窗，可以看到 Hello World 的確被印出了。

![syscall_helloworld](/images/rrxv6/syscall_helloworld.png)

現在我們應該更了解，在我們 C 程式寫 `printf("Hello World!");` 時，作業系統到底做了多少事了，真的是 Hello World 年年都會寫，每年都有不同的體會。

# 總結

這篇的總結我想來整理一下，在 xv6 開機到現在我們寫過比較特別的 return。

return 其實是一個有點 funny 的東西，對一般的程式設計師來說， function 最後要用 return 把東西丟回去是最基本的。  
精進一點，會知道 return address register 的存在~~可以透過改 return address 做壞壞的事~~。
如果修過某些計算機結構或是 [nand2tetris]({{<relref "nand2tetris_part2#week-2-branching-function-call">}})，
還會知道一個 ret 指令背後處理器做了多少東西。

riscv 有 ret, sret, mret 三種不同的 ret，rrxv6 裡面每個 ret 剛好都有兩種不同用法：

ret：
1. 正常的使用
2. [context switch]({{< relref "rrxv6_contextswitch">}})，我們手動修改 $ra 指向新 process 的 PC 再呼叫 ret，
也就是所謂的*透過改 return address 做壞壞的事*。

sret：
1. 從 Supervisor Mode trap handler 返回，從 sepc 叫出 trap 發生前正在執行的位址。
2. 設定 SPP 為 User Mode 後呼叫 sret，從 Supervisor Mode 進入 User Mode；sepc 也是手動修改，指向 User Mode 下要執行的位址。

mret：
1. 從 Machine Mode trap handler 返回，從 mepc 叫出 trap 發生前正在執行的位址。
2. 設定 MPP 為 Supervisor Mode 後呼叫 mret，[開機時從 machine mode 跳轉到 supervisor mode]({{< relref "rrxv6_stackpointer" >}})，mepc 的位址設定為 main function 的位址。

整理如下：
| 指令 | 位置 | 下一個執行位址 | 用途 |
|:-|:-|:-|:-|
| ret | any function end | Caller address in $ra | Function Return |
| ret | asm/switch.asm | proc.context 中新的 process 的 $ra | Context Switch |
| sret | asm/kernelvec.asm kernelvec | PC before trap in csr sepc | Return from Supervisor Mode trap handler |
| sret | asm/trampoline.asm userret | csr sepc -> user process PC | Supervisor Mode -> User Mode |
| mret | asm/kernelvec.asm timervec | PC before trap in csr mepc | Return from Machine Mode trap handler |
| mret | start.rs:start | csr mepc -> main function | Machine Mode -> Supervisor Mode|
