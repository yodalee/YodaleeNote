---
title: "rrxv6 : interrupt"
date: 2021-12-28
categories:
- rust
- operating system
tags:
- rust
- xv6
- riscv
- PLIC
series:
- rrxv6
images:
- /images/rrxv6/interrupt_gdb.png
forkme: rrxv6
---

故事是這樣子的，上一章的結尾雖然寫了：
> 下一步就可以開始初始化 kernel 的 process table 啦。

但事後發現，原來還有東西比建立 process 更重要的，那就是先把 trap 給建立好：

![trap](/images/rrxv6/trap.png)
<!--more-->

俗話說得好：~~Process 可以不跑，Trap 不能不接~~
trap 是作業系統非常重要的環節，讓硬體有事能通知 kernel 處理，沒有 trap 作業系統就沒辦法跟外界互動
（除非你要一個一個去輪詢…），我們這篇文就來處理一下 riscv 的 trap/interrupt。

# 重構 UART
首先是我們 interrupt 的來源，目前手上唯一有的對外裝置就是 UART 了，雖然本系列很早就設定好 UART，
但其實沒做任何初始化的設定，只是拿它當輸出工具，我們先來 refactor 一下。  

說是 refactor 其實就是多包一層 struct，這是從其他人 [實作嵌入式的文章](https://doc.rust-lang.org/stable/embedded-book/peripherals/a-first-attempt.html)
裡得到的寫法，`UartRegister` 對應底層的 register。

```rust
#[repr(C)]
struct UartRegister {
  thr: RW<u8>,
  ier: RW<u8>,
  isr: RW<u8>,
  lcr: RW<u8>,
  mcr: RW<u8>,
  lsr: RW<u8>,
  msr: RW<u8>,
  spr: RW<u8>,
}
```

struct `Uart` 帶著一個 `UartRegister`：

```rust
pub struct Uart {
  p: &'static mut UartRegister
}
```

所有需要操作 Uart Register 的行為都可以封裝到 Uart 裡面，包括之前看過的 putc, puts 等等，
新增的 init 函式會對 UART 埠進行初始化，包括設定 Baud rate、設定 FIFO 模式以及並開啟 Rx/Tx 的 interrupt；
`new` 函式則會呼叫 init 初始化對應的 UART 埠，new 函式設定為 private ，就只有這個檔案裡才能初始化 UART 埠：
```rust
impl Uart {
  fn new() -> Self {
    let mut uart = Uart {
      p: unsafe { &mut *(memorylayout::UART0 as *mut UartRegister) },
    };
    uart.init();
    uart
  }

  fn init(&mut self) {
    // disable interrupt
    self.set_interrupt(IerFlag::DISABLE);

    unsafe {
      // special mode to set baud rate
      self.p.lcr.write(LcrFlag::DLAB.bits());

      // set baud rate of 38.4K
      self.p.thr.write(0x03);
      self.p.ier.write(0x0);

      // set word length to 8 bits, no parity
      self.p.lcr.write(LcrFlag::LENGTH_8.bits());

      // reset and enable FIFOs
      self.p.isr.write((FcrFlag::FIFO_ENABLE | FcrFlag::FIFO_CLEAR_RX | FcrFlag::FIFO_CLEAR_TX).bits());
    }

    // enable transmit and receive interrupt
    self.set_interrupt(IerFlag::RX_ENABLE | IerFlag::TX_ENABLE);
  }
}
```

在這個模組裡，用 `lazy_static` 來生成唯一的一個 Uart 實例，也是 `Uart::new` 唯一會被呼叫到的地方，
之後作業系統要用 Uart 就會統一用這個實例來存取。  
```rust
lazy_static! {
  pub static ref UART: Mutex<Uart> = Mutex::new(Uart::new());
}
```

# PLIC

在 riscv 上PLIC (Platform-Level Interrupt Controller) 相當於 ARM NVIC，負責控管 riscv 上要接收的 interrupt，
將來自許多不同裝置的 external interrupt 整理起來，送到對應的 hart 上，
CPU 也可以用軟體操控要啟用/停用哪些 interrupt、設定 interrupt 的優先程度、標示 interrupt 是否已處理。  
這裡的參考資料，在 v1.10 可以看[規格書 The RISC-V Instruction Set ManualVolume II: Privileged Architecture](https://riscv.org/wp-content/uploads/2017/05/riscv-privileged-v1.10.pdf)，
v1.11 之後則被移掉了，最接近的規格變成在 [github riscv-plic-spec](https://github.com/riscv/riscv-plic-spec/blob/master/riscv-plic.adoc)上。

規格規定 PLIC 可以支援最多 1023 個 interrupt，interrupt 0 作為保留；另外有 15872 個 context，
interrupt 跟 context 的數量會隨實作而變動，但 register 的位移量必須要依規格而定。  
所謂的 context 依照 [spec 上的討論](https://github.com/riscv/riscv-plic-spec/issues/10)
意指一個可接受 interrupt 的 hart 模式，例如我們有三個 hart，每個 hart 有 Machine mode 和 Supervisor mode，則總共會有六個 context。  
這是否意味著有 machine/supervisor mode 的 riscv 最多只能有 7936 個核心？規格書沒有明說，我也不確定答案。

## PLIC register layout

PLIC 的規格定義下列的 register 位址，如上所述，即使支援的 interrupt, context 數量較少，位址還是要依照這個表設定：

| Block Offset | Subblock offset | Description | Note |
|:-|:-|:-|:-|
| 0x0 | | Reserved | |
| 0x4 - 0x1000 | | Interrupt 1~1023 priority | 4 bytes/interrupt |
| 0x1000 - 0x1080 | | Interrupt Pending Bit 1-1023 | 1 bit/interrupt |
| 0x2000 - 0x1F2000 | | Interrupt Enable Bit | 1024 bits/interrupt/context |
| | 0x2000 - 0x2080 | Enable bits for sources 0-1023 on context 0 | context 0 |
| | 0x2080 - 0x2100 | Enable bits for sources 0-1023 on context 1 | context 1 |
| | ................. | ........ | |
| | 0x1F1F80 - 0x1F2000 | Enable bits for sources 0-1023 on context 15871 | context 15871 |
| 0x1F2000 - 0x200000 | | Reserved | |
| 0x200000 - 0x400000 | | Priority threshold and Claim/Complete | 4096 bytes/context |
| | 0x200000 | Priority threshold for context 0 | context 0|
| | 0x200004 | Claim/Complete for context 0 | |
| | 0x200008-0x201000 | Reserved | |
| | 0x201000 | Priority threshold for context 1 | context 1 |
| | 0x201004 | Claim/Complete for context 1 | |
| | 0x201008-0x202000 | Reserved | |
| | ................. | ........ | |
| | 0x3FFF000 | Priority threshold for context 15871 | context 15871 |
| | 0x3FFF004 | Claim/Complete for context 15871 | |
| | 0x3FFF008-0x4000000 | Reserved | |

PLIC 支援的 priority 視實作而定，priority 0 為最低，表示不會觸發 interrupt，priority 1 則是最低會觸發的中斷；
如果有同 priority 的 interrupt 同時發生時，Interrupt ID 較低的 interrupt 會有較高的優先權。  
Interrupt Enable 寫入 1 表示一個 context 的一個 interrupt 被 enable 了。

# Trap 實作

在處理 interrupt 之前，我們要先設定處理器讓它知道由誰處理，
在 riscv 是由 csr stvec (Supervisor Trap-Vector Base-Address Register) 來記錄，stvec 的內容如下：

![stvec](/images/rrxv6/stvec.png)

stvec 模式設定為 Direct Mode 的時候，所有的 exception 與 interrupt 都會跳轉到 stvec 指定的位址；
如果是 Vectored Mode，synchronous exception 由指定位址處理，
interrupt 則是依 interrupt ID 跳到 `BASE + 4 * ID` 處理（這也是為什麼 interrupt 0 是保留的）。

我們先用 assembly 實作 interrupt handler kernelvec，內容其實很冗，就是先把所有的 registers 都壓進 stack，
呼叫函式 kerneltrap，然後再把 registers 全部吐出來。

```asm
.globl kerneltrap
.globl kernelvec
.option norelax
.align 4
kernelvec:
  # make room to save registers.
  addi sp, sp, -256

  # save the registers.
  sd ra, 0(sp)
  sd sp, 8(sp)
  sd gp, 16(sp)
  sd tp, 24(sp)
  sd t0, 32(sp)
  sd t1, 40(sp)
  sd t2, 48(sp)
  sd s0, 56(sp)
  sd s1, 64(sp)
  sd a0, 72(sp)
  sd a1, 80(sp)
  sd a2, 88(sp)
  sd a3, 96(sp)
  sd a4, 104(sp)
  sd a5, 112(sp)
  sd a6, 120(sp)
  sd a7, 128(sp)
  sd s2, 136(sp)
  sd s3, 144(sp)
  sd s4, 152(sp)
  sd s5, 160(sp)
  sd s6, 168(sp)
  sd s7, 176(sp)
  sd s8, 184(sp)
  sd s9, 192(sp)
  sd s10, 200(sp)
  sd s11, 208(sp)
  sd t3, 216(sp)
  sd t4, 224(sp)
  sd t5, 232(sp)
  sd t6, 240(sp)

  # call handler
  call kerneltrap

  # restore registers.
  ld ra, 0(sp)
  ld sp, 8(sp)
  ld gp, 16(sp)
  # not this, in case we moved CPUs: ld tp, 24(sp)
  ld t0, 32(sp)
  ld t1, 40(sp)
  ld t2, 48(sp)
  ld s0, 56(sp)
  ld s1, 64(sp)
  ld a0, 72(sp)
  ld a1, 80(sp)
  ld a2, 88(sp)
  ld a3, 96(sp)
  ld a4, 104(sp)
  ld a5, 112(sp)
  ld a6, 120(sp)
  ld a7, 128(sp)
  ld s2, 136(sp)
  ld s3, 144(sp)
  ld s4, 152(sp)
  ld s5, 160(sp)
  ld s6, 168(sp)
  ld s7, 176(sp)
  ld s8, 184(sp)
  ld s9, 192(sp)
  ld s10, 200(sp)
  ld s11, 208(sp)
  ld t3, 216(sp)
  ld t4, 224(sp)
  ld t5, 232(sp)
  ld t6, 240(sp)

  addi sp, sp, 256

  # return to whatever we were doing in the kernel.
  sret
```

接著就能把 kernelvec 註冊到 stvec 裡面：

```
extern "C" {
    fn kernelvec();
}

pub fn init_harttrap() {
  let mut stvec = Stvec::from_bits(0);
  stvec.set_addr(kernelvec as u64);
  stvec.write();
}
```

# PLIC 實作

對應前述 PLIC 的位址，我們在 memory layout 附上以下的位址：
```rust
pub const PLIC_BASE      : u64 = 0x0c000000;
pub const PLIC_PRIORITY  : u64 = PLIC_BASE + 0x0;
pub const PLIC_PENDING   : u64 = PLIC_BASE + 0x1_000;
pub const PLIC_ENABLE    : u64 = PLIC_BASE + 0x2_000;
pub const PLIC_THRESHOLD : u64 = PLIC_BASE + 0x200_000;
pub const PLIC_CLAIM     : u64 = PLIC_BASE + 0x200_004;
```

實作對應的函式，我用一個空的 Plic struct 包裹住所有的函式，這是為了 include 方便，不用一個函式一個函式引入，
反正經過 release 的最佳化之後，struct 也會直接被最佳化掉（事實上連下面函式都被 inline 到 main 裡面去了）。
PLIC 會需要的函式包括：

* set_priority：設定 PLIC_PRIORITY， interrupt priority
* set_enable/set_disable：設定 PLIC_ENABLE，enable bit
* set_threshold：設定 PLIC_THRESHOLD
* get_claim：讀取 PLIC_CLAIM，會讀到目前的 interrupt number
* set_complete：寫入 PLIC_CLAIM，告訴 PLIC 我們已經處理完這個 interrupt

實作如下，每個函式會算出對應的位址並寫入，另一個實作方法是用 rust 的 [volatile_register](https://docs.rs/volatile-register/latest/volatile_register/)
預先在 struct 的對應位址上產生 `RW`，不過 PLIC 對應的區塊實在太大了，
還要視實作的 interrupt 數量跟 context 數量來調整，決定先不這樣實作：

```rust
/// set id interrupt priority, zero is disabled
pub fn set_priority(&self, id: u64, priority: u32) {
  let addr = (PLIC_BASE + 4 * id) as *mut u32;
  unsafe {
    core::ptr::write_volatile(addr, priority);
  }
}

/// Set interrupt enable
pub fn set_enable(&self, hart: u64, context: PlicContext, id: u64) {
  assert!(id < MAX_INTERRUPT);
  let addr = (PLIC_ENABLE +
    hart * 0x100 +
    (context as u64) * 0x80 +
    (id / 32)) as *mut u32;
  unsafe {
    let val = core::ptr::read_volatile(addr);
    core::ptr::write_volatile(addr, val | (1u32 << (id % 32)));
  }
}

/// Set interrupt enable
pub fn set_disable(&self, hart: u64, context: PlicContext, id: u64) {
  assert!(id < MAX_INTERRUPT);
  let addr = (PLIC_ENABLE +
    hart * 0x100 +
    (cntext as u64) * 0x80 +
    (id / 32)) as *mut u32;
  unsafe {
    let val = core::ptr::read_volatile(addr);
    core::ptr::write_volatile(addr, val & !(1u32 << (id % 32)));
  }
}

/// Set threshold of interrupt of (hart, context)
pub fn set_threshold(&self, hart: u64, context: PlicContext, threshold: u32) {
  let addr = (PLIC_THRESHOLD +
    hart * 0x2000 +
    (context as u64) * 0x1000) as *mut u32;
  unsafe {
    core::ptr::write_volatile(addr, threshold);
  }
}

/// Get PLIC current interupt id
pub fn get_claim(&self, hart: u64, context: PlicContext) -> u32 {
  let addr = (PLIC_CLAIM +
    hart * 0x2000 +
    (context as u64) * 0x1000) as *mut u32;
  unsafe {
    core::ptr::read_volatile(addr)
  }
}

/// Mark irq complete
pub fn set_complete(&self, hart: u64, context: PlicContext, id: u32) {
  assert!((id as u64) < MAX_INTERRUPT);
  let addr = (PLIC_CLAIM +
    hart * 0x2000 +
    (context as u64) * 0x1000) as *mut u32;
  unsafe {
    core::ptr::write_volatile(addr, id);
  }
}
```

在 main 函式裡面利用這些函式設定 PLIC。

依照[這篇文](https://ithelp.ithome.com.tw/articles/10270210)所述，在 qemu riscv 實作的 [virt 機器 UART interrupt 設定](https://github.com/qemu/qemu/blob/master/include/hw/riscv/virt.h#L67-L74)，
UART 的 interrupt 編號為 10，我們將對應的 priority 設為 1、設定 supervisor interrupt 10 為 enable 以及 supervisor threshold 為 0。

```rust
let plic = Plic::new();
plic.set_priority(UART0_IRQ, 1);
plic.set_enable(hart, PlicContext::Supervisor, UART0_IRQ);
plic.set_threshold(hart, PlicContext::Supervisor, 0);
```

除了這個之外，還要設定 csr sstatus：

![sstatus](/images/rrxv6/sstatus.png)

bit 1 SIE (Supervisor Interrupt Enable) 控制所有 supervisor level 的 interrupt：
```rust
pub fn intr_on() {
  let mut sstatus = Sstatus::from_read();
  sstatus.enable_interrupt(Mode::SupervisedMode);
  sstatus.write();
}
```

最後一個是 csr SIE(也叫 Supervisor Interrupt Enable)，這個在[作業系統初始化的時候]({{< relref 2021_rrxv6_stackpointer>}}) 已經把 Supervisor Software/Timer/External Interrupt 都打開了。

如此就設定好 PLIC了。  

# Interrupt Handler

現在來實作處理 interrupt 的 kerneltrap，因為要讓 assembly 連結得到，這個函式加上`#[no_mangle]`：
```rust
#[no_mangle]
pub fn kerneltrap() {
  let sepc = Sepc::from_read();
  let sstatus = Sstatus::from_read();

  if sstatus.get_spp() != Mode::SupervisedMode {
    panic!("kerneltrap: not from supervised mode");
  }
  if sstatus.get_sie() {
    panic!("kerneltrap: interrupts enabled");
  }

  interrupt_handler();

  sepc.write();
  sstatus.write();
}
```

interrupt_handler 會去讀取 csr scause，MSB 記錄是不是 interrupt，剩餘的 63 bits 則是 exception code，
如果我們拿出來是 external interrupt，就會去問 PLIC claim 看看現在的 irq code，並跟 plic 註冊處理完成。

![scause](/images/rrxv6/scause.png)

```rust
pub fn interrupt_handler() {
  let plic = Plic::new();
  let scause = Scause::from_read();
  let hart = get_cpuid();

  if scause.is_interrupt() &&
    scause.get_code() == Interrupt::SupervisorExternal as u64 {
    let irq = plic.get_claim(hart, PlicContext::Supervisor);

    if irq != 0 {
      plic.set_complete(hart, PlicContext::Supervisor, irq);
    }
  }
}
```

在 interrupt handler 我這邊是沒做任何處理，測試的時候我曾經讓 uart 在這裡吐一個字元，然後就進到我自稱的**中斷劫**裡：
1. UART 發送一個 interrupt
2. Interrupt handler 叫 UART 發送一個字元
3. UART 發送一個字元，並發出一個 TX interrupt

然後程式就出不來了。  

另外，如果我們把 `plic.set_complete` 這行拿掉，那一樣會進到劫裡面，因為 PLIC 不知道你有沒有處理這個中斷，
就一直對處理器送中斷的信號，處理器就陷在 interrupt handler 裡了。

# 測試

同樣一邊跑 qemu，一邊打開 gdb ，中斷點設定在 `interrupt_handler` 及 `get_claim`。  

![interrupt_gdb](/images/rrxv6/interrupt_gdb.png)

第一次發現會一直收到 timer interrupt，原來早先實作的 machine trap handler `timervec` 裡面，
收到 timer interrupt 之後，會寫入 csr SIP 來觸發 supervisor 的 software interrupt。

為了測試先把這段拿掉，可以看到的確進入 interrupt_handler，這是我在印出 OS 啟動訊息時留下來的 TX interrupt；
從 get_claim 會得到 UART interrupt id = 10。  
繼續執行就不會有任何 interrupt，直到我們在 qemu 按下鍵盤觸發中斷，才會再敲入 interrupt_handler 中。

# 結語

本章實作了 PLIC 的控制，並且設定 supervisor interrupt handler 來處理 riscv 的 interrupt。

實作了這麼多，我們可以來個小小的整理，從你按下鍵盤到處理器裡面處理這個按下的字元（先不考慮什麼鍵盤是 USB 或我們是用 qemu），
在 riscv 上面總共經過哪些步驟或檢查，感覺這很適合出一個考題~~這裡是重點之後會考~~：

1. 事件發生，例如 UART 收到字元，至於它怎麼收到字元？請看小弟拙作 [Open FPGA 系列 - UART]({{<relref openfpga_uart>}})
2. UART 硬體檢查 IER，RX Interrupt 是否被設定，有的話就往 PLIC 發出一個中斷
3. PLIC 收到 Interrupt，檢查 enable bit 是否寫入，priority 是否高於 threshold，皆是則對 context
（machine mode 和 supervisor mode 分屬不同 context）發出 external interrupt
4. Hart 收到 external interrupt，檢查 csr sstatus 是否有 enable interrupt
5. Hart 檢查 csr sie 是否有 enable external interrupt，若有則中斷目前執行中的程序
6. 中斷發生，從 stvec 叫出 trap handler address 覆寫掉 program counter PC，另外還有一些 csr update，
scause 中寫入中斷原因，sstatus SPP 寫入目前的執行權限
7. 處理器進入 kernelvec 執行我們寫的處理程序

以上，希望能有把 trap 的發生與處理解釋清楚。
