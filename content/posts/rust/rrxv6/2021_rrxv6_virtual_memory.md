---
title: "rrxv6 : virtual memory"
date: 2021-12-14
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
- /images/rrxv6/translate.png
forkme: rrxv6
latex: true
---

上次我們發佈 rrxv6 的文章，已經是八月的事情了，大家可能以為我已經棄更了？
其實這個小弟也有在認真反省，在我停更 rrxv6 這段期間剛好看到傳說中的 jserv 大神貼文：

> 到底高等教育出了什麼問題？為何很大比例的電機資訊畢業生，沒辦法堅持把事情做好？  
> 思索九年，我想自己理解部分的原因：扎實地做事難以獲得短期的讚揚，而台灣許多人無法等到長期效益落實的那刻……。

想說靠北這不就是在說我嗎QQ，一直以來都沒把事情做好，像 ruGameboy 最後就被我棄更了，現在變成十八般武藝樣樣稀鬆只能混口飯吃。

<!--more-->

所以說為什麼會停更這麼久？大致歸納有下面幾個理由：

1. 如上所述我跑去玩 [FPGA](https://yodalee.me/series/fpga/) 了，然後又花了點時間學了一下 systemC。
2. 在寫 memory allocator 的時候，發現所用的 linked list allocator 有一個實作上的缺陷，發了
[一個 issue](https://github.com/phil-opp/linked-list-allocator/issues/53) 跟 
[pull request](https://github.com/phil-opp/linked-list-allocator/pull/54) 把它修掉，
理論上如果大量配置記憶體，這個 fix 能讓 allocation 的速度快上不少。
3. 這關要實作的部分是 virtual memory，剛好是作業系統裡面相當困難的一關，再加上在 Rust 用 pointer 的嚴格限制讓我不斷卡關，
我大概從 11/17 開工，到 12/9 左右才初步破關完成。

這篇文章會著重在虛擬記憶體，我會 PageTable 並 map 數個虛擬位址，開啟虛擬位址，然後在虛擬位址下使用 UART。  
以下依序講解：
1. riscv 虛擬記憶體的設計。
2. 從上一回 memory allocator 之後我又改了什麼
3. 如何封裝 virtual memory 的各個結構
4. 建構 Page Table
5. 如何操作 Rust 裡面極少使用的 pointer
6. 結語

# riscv 虛擬記憶體

~~在目前世界線的收束~~，管理記憶體上，虛擬記憶體搭配分頁（page）是目前所有處理器/作業系統的標準作法。  
簡單來說，記憶體的位址會分為兩種，實體記憶體位址（physical）和虛擬記憶體位址（virtual）；
虛擬記憶體會透過分頁表的方式，將虛擬記憶體的位址轉換到某個實體記憶體上面。

riscv 目前提供以下幾種模式：
* riscv 32 bits：sv32
* riscv 64 bits：sv39 - 3 層 page table
* riscv 64 bits：sv48 - 4 層 page table
* riscv 64 bits：sv57 - 5 層 page table，尚未定案

另外未來可能會有對應 6 層 page table 的 sv64 模式，這裡就暫不討論了。

直接用 spec 4.4 Sv39: Page-Based 39-bit Virtual-Memory System 的圖片來說明 sv39：
![sv39](/images/rrxv6/sv39.png)

虛擬記憶體定址長度為 39 bits（所以叫 sv39）；LSB 12 bits 會直接從虛擬位址映射到實體位址，
往上的 9 bits 為 VPN(Virtual Page Number) 0, 1, 2，對應 Page Table 內的 offset，
每一層的 page table 都有 512 個 entry，需要的 size 為 512 * 8 (64 bits) = 4096 bytes。

在最後一層的 page table，裡面存的就是圖下的 page table entry， 內容有三層的 PPN (Physical Page Number) 
和對應的 flag， 可以從 PPN 配上 virtual address LSB 的 page offset 得到實體位址。

flag 的說明在 4.3.1 sv32 的部分有說明：
* V: Valid，PTE 是否有效。
* RWX: Read/Write/Execute，只有 leaf PTE 會設定 RWX flag。
* U: 是否可從 user mode 存取。
* G: Global mapping。
* A: Access PTE 在 A flag clear 之後曾被存取。
* D: Dirty PTE 在 Dirty clear 之後曾被寫入。

G, A, D 三個 flag 在 xv6 的實作中並沒有用到。

在各模式之下，分頁表所需的空間以及可管理的記憶體如下表所示：
|   |分頁表空間|可管理記憶體空間|
|:-|:-|:-|
|sv39|~=1 GB|512 GB|
|sv48|~=512 GB|256 TB|
|sv57|~=256 TB|128 PB|

其實這個還滿好算的，sv39 因為有三層 table，每個分頁表 4096 bytes，所需空間為：
$$ (1 + 2^{9} + 2^{18}) \times 4K \approx 1 GB $$  
所管理的空間則是：
$$ 2^{39} = 512 GB $$
當然，就目前人類技術的限制顯然是不需要用到 PB 等級的記憶體啦，
我查到目前最大也才 160 TB **而已**，也許也是因為這樣 sv57 才*還*沒有寫入正式標準。

## satp
其實這個東西已經有出現過了，全名是 SATP (Supervisor Address Translation and Protection)，
或是過去曾稱為 SPTBR (Supervisor Page-Table Base Register)，它的地位相當於 x86 的 CR0 和 CR3；或是 ARM 裡面的 TTBCR。

在我們[一開始初始化作業系統]({{< relref "2021_rrxv6_stackpointer" >}})的時候，
會把 csr satp 寫入 0 關掉 virtual memory，在 4.1.12 描述 satp 的內容。

![satp](/images/rrxv6/satp.png)

* bit 60-63 表示目前的 virtual memory 模式，未來我們要用 sv39 的 0x8 取代沒有 virtual memory 的 0x0。
* bit 0-43 則是 root page table 省略 LSB 12 bits 的實體位址。

如果把 sv39 模式之下，從虛擬記憶體變換成實體記憶體的流程畫成圖，大概是長這個樣子，
雖然這張圖在所有的作業系統課本應該都會出現，不過我還是重畫了：
![translate](/images/rrxv6/translate.png)

另外，這個部分我發現有另一篇用 golang 實作 riscv kernel 的鐵人賽文章
[予焦啦！RISC-V 虛擬記憶體機制簡說 ](https://ithelp.ithome.com.tw/articles/10267494) 講解得十分清楚，大家可以多多參考。

# 前置準備

從上次我們完成 memory allocator 之後，到現在實作 virtual memory，有一些前置準備可以先做：

## Panic 資訊
有了 memory allocator，我們可以在 code 裡面插入動態配置的記憶體，例如
```rust
let b = Box::new(64);
```
除此之外，我們也可以使用 alloc 提供的 format! 來格式化字串，
例如 panic 函式的參數有一個 [PanicInfo](https://doc.rust-lang.org/std/panic/struct.PanicInfo.html)，
裡面會有我們送給 `panic!` 的資訊，現在就可以用 `format!` 把這個資訊取出來了。
```rust
fn panic(panic_info: &PanicInfo<'_>) -> ! {
  let m_uart = uart::read();
  m_uart.puts(&format!("{}", panic_info));
  loop {}
}
```

未來我們就能使用諸如 `panic!("mappages error")` 讓 kernel crash 的時候能顯示出明確的原因。

## csr 移到單獨的 library

另外我也把操作 csr 的 library 獨立出去了，這個原因是我對每一個 csr 都提供了諸如 read, write 等函式，
但只要我沒用到的，它在編譯的時候都會吐一堆警告訊息，覺得很煩就把它們搬出去了。  
原始碼移動到這個 library：[rv64](https://github.com/yodalee/rv64)

# 封裝 virtual memory 結構

在實際映射虛擬記憶體之前，我們要先把資料結構給架起來，
這部分我大量參考了 [rust-osdev/x86_64](https://github.com/rust-osdev/x86_64) 的函式庫，有些部分已經接近照抄了。

## PteFlag

將先前提到的 Flag 給虛擬化，可以輕鬆的用 [bitflags](https://docs.rs/bitflags/latest/bitflags/) 完成：
```rust
use bitflags::bitflags;

// bit flag for page permission
bitflags! {
  pub struct PteFlag: u64 {
    const PTE_VALID = 0x01;
    const PTE_READ  = 0x02;
    const PTE_WRITE = 0x04;
    const PTE_EXEC  = 0x08;
    const PTE_USER  = 0x10;
    const PTE_GLOB  = 0x20;
    const PTE_ACCES = 0x40;
    const PTE_DIRTY = 0x80;
  }
}
```

## VirtAddr

VirtAddr 是 u64 的封裝，因為 riscv 的 spec 有明定：

> Load and store effective addresses, which are 64 bits,
> must have bits 63–39 all equal to bit 38, or else a page-fault exception will occur.

我們可以拿一個 u64 當作 Virtual Address 來使用，但這樣就少了一層保護，只要使用者拿一個不合法的位址，
kernel 就會被硬體踢進 page-fault exception。  
對 Rust 這種強型別語言來說，型別的重要度可能佔到 50% 以上，雖然有點像多此一舉，但像這樣封裝基本型態可說是必須的一步。

```rust
#[derive(Clone,Copy,PartialEq,Eq,PartialOrd,Ord)]
pub struct VirtAddr(u64);
```

封裝 u64 之後，就可以在型別提供的函式上，加上合法位址的檢查，或者利用 new_truncate 來生成合法的位址。

```rust
impl VirtAddr {
  VirtAddr  new(addr: u64) -> Self {
    Self::try_new(addr)
      .expect(&format!("Virtual address in riscv should have bit 39-63 copied from bit 38 {}", addr))
  }

  pub fn try_new(addr: u64) -> Result<VirtAddr, InvalidVirtAddr> {
    match addr.get_bits(38..64) {
      0 | 0x3ffffff => Ok(VirtAddr(addr)),   // valid address
      1 => Ok(VirtAddr::new_truncate(addr)), // address need sign extend
      _ => Err(InvalidVirtAddr{}),
    }
  }

  pub fn new_truncate(addr: u64) -> Self {
    Self(((addr << 25) as i64 >> 25) as u64)
  }
}
```

## PageTableIndex

同樣的，把 u16 封裝成 PageTableIndex 型別：

```rust
// 4096 bytes / 8 bytes per entry = 512 entries
const ENTRY_COUNT: usize = 512;

pub struct PageTableIndex(u16);

impl PageTableIndex {
pub fn new(index: u16) -> Self {
  assert!((index as usize) < ENTRY_COUNT);
    Self (index)
  }

  pub const fn new_truncate(index: u16) -> Self {
     Self(index % ENTRY_COUNT as u16)
  }
}
```

## PageTableLevel

用 primitive number 代表現在所在的階層？不行，用 enum。

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum PageTableLevel {
  Zero = 0,
  One,
  Two,
  Three, // only valid in sv48
}

impl PageTableLevel {
  pub const fn next_level(self) -> Option<Self> {
    match self {
      PageTableLevel::Three => Some(PageTableLevel::Two),
      PageTableLevel::Two   => Some(PageTableLevel::One),
      PageTableLevel::One   => Some(PageTableLevel::Zero),
      PageTableLevel::Zero  => None,
    }
  }
}
```

搭配 `PageTableLevel` ，在 `VirtAddr` 裡面實作取得 `PageTableIndex` 的函式：

```rust
impl VirtAddr {
  pub const fn p0_index(self) -> PageTableIndex {
      PageTableIndex::new_truncate((self.0 >> 12) as u16)
  }

  pub const fn p1_index(self) -> PageTableIndex {
      PageTableIndex::new_truncate((self.0 >> 9 >> 12) as u16)
  }

  pub const fn p2_index(self) -> PageTableIndex {
      PageTableIndex::new_truncate((self.0 >> 9 >> 9 >> 12) as u16)
  }

  pub const fn p3_index(self) -> PageTableIndex {
      PageTableIndex::new_truncate((self.0 >> 9 >> 9 >> 9 >> 12) as u16)
  }

  pub const fn get_index(self, level: PageTableLevel) -> PageTableIndex {
      match level {
        PageTableLevel::Zero  => self.p0_index(),
        PageTableLevel::One   => self.p1_index(),
        PageTableLevel::Two   => self.p2_index(),
        PageTableLevel::Three => self.p3_index(),
      }
  }
}
```

## PageTableEntry

`PageTable` 裡面存的 `PageTableEntry` 也是 u64 的封裝

```rust
pub struct PageTableEntry {
  entry: u64
}

impl PageTableEntry {
  pub const fn is_unused(&self) -> bool {
    self.entry == 0
  }

  pub fn addr(&self) -> u64 {
    (self.entry >> 10) << 12
  }

  pub fn set_addr(&mut self, addr: u64, perm: PteFlag) {
    self.entry = addr | perm.bits();
  }
}
```

## PageTable

最後是 `PageTable`，封裝 `PageTableEntry` 陣列，實作使用 `PageTableIndex` 來對陣列取值：

```rust
pub struct PageTable {
  entries: [PageTableEntry;ENTRY_COUNT]
}

impl PageTable {
  /// Create empty PageTable
  #[inline]
  pub const fn new() -> Self {
    const EMPTY: PageTableEntry = PageTableEntry::new();
    Self {
      entries: [EMPTY;ENTRY_COUNT]
    }
  }
}

impl Index<PageTableIndex> for PageTable {
  type Output = PageTableEntry;
  #[inline]
  fn index(&self, index: PageTableIndex) -> &Self::Output {
    &self.entries[usize::from(index.0)]
  }
}

impl IndexMut<PageTableIndex> for PageTable {
  #[inline]
  fn index_mut(&mut self, index: PageTableIndex) -> &mut Self::Output {
    &mut self.entries[usize::from(index.0)]
  }
}
```

準備完成，現在我們把這些物件組起來，來實作 rrxv6 的 virtual memory。

# rrxv6 virtual memory 實作

## kalloc

這是 alloc 函式的一個封裝，幫我們分配一塊 align 於 4096 bytes，大小為 4096 bytes 的記憶體並寫成空白的，
因為 rust 在離開 scope 的時候會自動刪除分配的記憶體，因此我們無法使用 rust new 來實作。

```rust
pub fn kalloc() -> *mut u8 {
  unsafe {
    let layout = Layout::from_size_align(PAGESIZE as usize, 4096).unwrap();
    let ptr = alloc(layout);
    write_bytes(ptr, 0x0, PAGESIZE as usize);
    return ptr;
  }
}
```

## map_page

map_page 負責把一個 virtual address 映射到 physical address，level 會指示現在是在第幾層 page table。  
從 page_table 拿出 pte 之後，會依照現在的 level，如果已經是 leaf pte，會把實體位址與 PteFlag 寫入 pte。
反之如果還有下一層，則 pte 記錄的是下一層 page table 的位址，得到 page table 之後，遞迴呼叫 map_page 進行下一層的映射。

```rust
fn map_page(page_table: &mut PageTable, va: VirtAddr, pa: u64, perm: PteFlag, level: PageTableLevel) -> Result<(), &'static str> {
  if va >= VirtAddr::new(MAXVA) {
    return Err("map_page: virtual address over MAX address")
  }

  let index = va.get_index(level);
  let pte = &mut page_table[index];
  match level.next_level() {
    None => {
      // Recursive end, write pte or error because of remap
      if pte.is_unused() {
        pte.set_addr((pa >> 12) << 10, perm | PteFlag::PTE_VALID);
        Ok(())
      } else {
        Err("map_page: remap")
      }
    },
    Some(next_level) => {
      // Allocate space for page table and call map_page with next level
      if pte.is_unused() {
        let ptr = kalloc();
        if ptr == 0 as *mut u8 {
          Err("kalloc failed in map_page")
        }
        let addr = ptr as *const _ as u64;
        pte.set_addr((addr >> 12) << 10, PteFlag::PTE_VALID);
      }
      let next_table = unsafe { &mut *(pte.addr() as *mut PageTable) };
      map_page(next_table, va, pa, perm, next_level)
    }
  }
}
```

## map_pages

與 map_page 類似，map_pages 會映射不止一個 Page 的記憶體。

```rust
fn map_pages(va: VirtAddr, mut pa: u64, size: u64, perm: PteFlag) -> Result<(), &'static str> {
  let page_table = unsafe { get_root_page() };
  let va_start = va.align_down();
  let va_end = VirtAddr::new_truncate(va.as_u64() + size - 1).align_down();
  let mut page_addr = va_start;

  while true {
    map_page(page_table, page_addr, pa, perm, PageTableLevel::Two)?;
    if page_addr == va_end {
      break;
    }
    page_addr += PAGESIZE;
    pa += PAGESIZE;
  }

  Ok(())
}
```

## kvm_map

kvmmap 負責呼叫 map_pages 並做好意外處理（呼叫 panic XD）。

```rust
fn kvmmap(va: VirtAddr, pa: u64, size: u64, perm: PteFlag) {
  match map_pages(va, pa, size, perm) {
    Ok(_) => {},
    Err(e) => panic!("mappages error: {}", e),
  }
}
```

## init_kvm

kernel page table 必須要在所有 CPU 之間共享，理所當然的是 rust 人人聞之色變的 global 變數，
跟之前一樣我們使用 lazy_static 封裝 KERNELPAGE 變數。  
這裡要說明一下，為什麼 KERNELPAGE 不是存一個 PageTable 物件而是 u64 呢？
因為我不知道該如何從 lazy_static 取出裡面物件的位址……，因此退而求其次存一個 u64 的位址在裡面。

```rust
lazy_static! {
  static ref KERNELPAGE: Mutex<u64> = Mutex::new(0);
}
```

在 init_kvm 會呼叫 kalloc 生成 root page table，把它的位址存入 KERNELPAGE 裡面；
另外我們實作一個 get_root_page 來取得儲存的位址，在上面的 map_pages 我們就用它來得到 root page table。

```rust
pub fn init_kvm() {
  let root_page: &mut PageTable = unsafe { &mut *(kalloc() as *mut PageTable) };
  let mut root_page_lock = KERNELPAGE.lock();
  *root_page_lock = root_page as *const _ as u64;
  drop(root_page_lock); // remember to drop the lock

  // call kvm_map…
}

pub unsafe fn get_root_page() -> &'static mut PageTable {
  let addr = *KERNELPAGE.lock();
  let ptr: *mut PageTable = addr as *mut PageTable;
  &mut *ptr
}
```

在 xv6，init_kvm 會映射下列幾塊記憶體：
| block | Physical Adress |
|:-|:-|
| UART |0x1000_0000 |
| virtio mmio disk interface | 0x1000_1000 |
| PLIC | 0x0C00_0000 |
| Kernel Text/Data | 0x8000_0000 |
| User process stack | |


先求會動，這裡映射 UART、Kernel text、Kernel data、還有 trampoline 四個區域：

```rust
kvmmap(VirtAddr::new(UART0), UART0, PAGESIZE,
  PteFlag::PTE_READ | PteFlag::PTE_WRITE);
kvmmap(VirtAddr::new(KERNELBASE), KERNELBASE, petext - KERNELBASE ,
  PteFlag::PTE_READ | PteFlag::PTE_EXEC);
kvmmap(VirtAddr::new(petext), petext, PHYSTOP as u64 - petext,
  PteFlag::PTE_READ | PteFlag::PTE_WRITE);
kvmmap(VirtAddr::new(TRAMPOLINE), ptrampoline, PAGESIZE, 
  PteFlag::PTE_READ | PteFlag::PTE_EXEC);
```

## init_page

當我們準備好 PageTable，最後一關就是打開 virtual memory 了。  
`init_page` 函式會設定 csr satp，設定為 sv39 mode，並寫入 root page table 的 address，在寫入之後，
要呼叫[sfence.vma](https://ithelp.ithome.com.tw/articles/10271097) 指令將 TLB 清空，就成功進入 virtual memory 了。

```rust
pub fn init_page() {
  let mut satp = Satp::from_bits(0);
  let ptr = unsafe { get_root_page() };
  satp.set_mode(SatpMode::ModeSv39);
  satp.set_addr(ptr as *const _ as u64);
  satp.write();
  sfence_vma();
}
```

## 實測

這次實測之前我先把我之前寫的奇怪的 scheduler 都刪掉了，只留下一行 uart，會印出 "OS started"。  
使用 qemu 模擬之後，雖然我們 kernel data 的部分映射比較多的記憶體，因此要跑一段時間，
但的確看到這行文字被印出來了，表示我們成功啟動虛擬記憶體啦 T_T。

![entervm](/images/rrxv6/entervm.png)

註：如果虛擬記憶體設定有錯，例如 UART 區段的記憶體沒有映射，在印出文字的時候，就會觸動到硬體的記憶體保護讓 kernel 當掉。  
我實測的時候它甚至讓我的 gdb 都 crash 掉，一時之間都不知道怎麼 debug 才好。

# 在 Rust 使用 pointer

在這次的實作裡面，可以看到我們大量的操作 rust 裡面極少出現的 pointer，像是：
```rust
let next_table = unsafe { &mut *(pte.addr() as *mut PageTable) };
let root_page: &mut PageTable = unsafe { &mut *(kalloc() as *mut PageTable) };
satp.set_addr(ptr as *const _ as u64);
```

在此之前我也曾被卡了非常久，參考官方的[說明文件](https://doc.rust-lang.org/reference/types/pointer.html)，
以及一些 stack overflow 的文章才解掉。  

簡而言之的規則是這樣的：  
所有的 rust 變數，都有一個對應的型別。  
我們宣告了變數，然後要把它傳到其他函式裡，如果這個型別沒有實作 Copy 屬性 `#[derive(Copy)]` 的話，
它是沒有辦法複製，函式的參數就必須使用 reference。
reference 是 rust 裡最常用的概念，包含常見的 shared reference (&) 和 mutable reference (&mut) ，
它代表的就是對該變數的參考。  
我們看到的 raw pointer，也有兩個對應的 *const T 跟 *mut T，這在 rust 裡面非常不建議使用，
用 `*` dereference raw pointer 是 unsafe operation。

在轉換上，用 T, &, pointer 分別代表實體資料、參考與指標，我歸納幾個可能會用到的物件轉換如下：
* T -> &: 實體型別到參考，這非常常用，是 rust 必備
```rust
let mut x: u32 = 42;
let y: &mut u32 = &mut x;
```
* T -> pointer，這個是可以，但是最好知道你在做什麼，下面這個會生出一個指向位址 42 的 pointer。  
```rust
let z = x as *const u64;
```
* & -> pointer，這裡我們不用寫型別，會從 reference 的型別去推斷  
```rust
let mut x: u32 = 42;
let ptr = &x as *const _;
```
* pointer A -> pointer B，這是（唯一？）修改型別的方式，rust 只允許兩種型別的改動  
1. primitive type 像 u32 as u64
2. trait object 在 base/derive 間轉換

pointer 則不受此限，如上面的 `kalloc() as *mut PageTable` 從 *mut u8 轉型為 *mut PageTable。

* pointer <-> address：所謂的 address 其實就是一個 u64 的數值，可以從 pointer 轉換或轉換為 pointer。
```rust
pte.addr() as *mut PageTable
ptr as *const _ as u64
```

# 結語

結語我想還是來比較一下，用 C (xv6) 跟 Rust (rrxv6) 實作的差別，如果你去看 xv6 的實作，
會發現它裡面只有一個特化的 pagetable_t ，而它其實是用：
```c
typedef uint64* pagetable_t
```
生成的，也就是說 xv6 它根本就沒有什麼型別的概念，它在映射記憶體的步驟，用口語描述就會是這樣：  
> 從 pagetable 所在的位址，offset virtual address 所帶的 index，
> 把這個位址的值轉型成一個 uint64 pointer，作為下一個 pagetable。

我們的實作則是：  
> 從位址轉型成 PageTable，VirtAddr va 透過函式取得 PageTableIndex，PageTable 取 \[PageTableEntry\] 
> 在 PageTableIndex 的 PageTableEntry 出來，將它的內容轉型成 PageTable。

可以看到型別在 Rust 實作上具有重要的意義，我覺得 Rust 的實作，其實就是封裝足夠多的型別，
說服 compiler 你對這些型別的操作都是沒有問題的。  
雖然這會讓（如同這篇文所示）實作時要下的工夫遠比 C 還要多，但下過工夫之後， compiler 一但放行，
通常也代表你在型別邏輯上沒有**不明顯**的問題。

----

在這章我們完成虛擬記憶體的初始化，下一步就可以開始初始化 kernel 的 process table 啦。
