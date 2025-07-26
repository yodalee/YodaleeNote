---
title: "rrxv6 : Memory Allocator"
date: 2021-08-08
categories:
- rust
- operating system
tags:
- rust
- xv6
- riscv
series:
- rrxv6
forkme: rrxv6
aliases:
- /2021/08/2021_rrxv6_allocator/
---

故事是這樣子的，雖然在上上篇的 [Context Switch]({{<relref "rrxv6_contextswitch" >}}) 我們曾經預告過因為 static 的問題，
可能要停更一段時間，但後來沒停更，static 問題很快就用 spin 提供的 no_std Mutex 解決了。  
不過，no_std Mutex 雖然解決 static 不用手爆 constructor 的問題，同時卻產生了另一個問題：stack overflow。

因為呼叫 static variable constructor 會用到 os process 的 stack，static variable size 一大，os process 的 stack 就會被吃乾抹淨。  
所以問題來了，我們必須要儘可能的縮小 static variable 的尺寸，像上篇把 process 的 context 全塞在裡面是不可能的
（為了讓 code 動起來我把 process 數量降到剩 2 個），因此下一步就很清楚了，必須挑戰作業系統裡一大難題：**記憶體管理**。
<!--more-->

這個問題說難不難，我最早看到用 rust 寫 OS 的 [blog_os](https://os.phil-opp.com/)，
作者自己就有公佈一款 [linked list allocator](https://github.com/phil-opp/linked-list-allocator)，
理論上我可以直接在 Cargo 上引用這個 repository，然後插到我的 project 即可。  
當然，除了直接用人家的 project ，我們還是要看一下 Rust 的記憶體管理是怎麼實作的，這篇我們就實作一個只能 alloc 不能 dealloc 的記憶體管理
（其實這樣說起來，我在 [Mutex]({{< relref "rrxv6_lazystatic_spin" >}}) 都自己實作才對，不該直接用 spin 提供的）。

# Global Allocator

rust 在設計上，記憶體管理是透過 [Global Allocator](https://blog.rust-lang.org/2018/08/02/Rust-1.28.html#global-allocators) 來處理，一般有 std 下會使用 std::alloc 的 System allocator，像我們這樣沒有 Global Allocator 的程式，是無法使用 heap 的，現下的 OS 在呼叫 Box 的時候：
```rust
extern crate alloc;
use alloc::boxed::Box;

let b = Box::new(64);
```

會出現如下錯誤：
```txt
error: no global memory allocator found but one is required;  
link to std or add `#[global_allocator]` to a static item that implements the GlobalAlloc trait.
```

錯誤訊息說得很明白了，要提供一個實作 [GlobalAlloc trait](https://doc.rust-lang.org/stable/std/alloc/trait.GlobalAlloc.html) 的 struct，為它加上 `#[global_allocator]` 這個 attribute。

```rust
extern crate alloc;
use alloc::alloc::{GlobalAlloc, Layout};

pub struct HeapAllocator;
```

GlobalAlloc trait 裡面定義了四個函式，必要的函式為前兩個 alloc 與 dealloc，rust 會自動幫我們推出 alloc_zeroed 跟 realloc：
```rust
pub unsafe trait GlobalAlloc {
  unsafe fn alloc(&self, layout: Layout) -> *mut u8;
  unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout);

  unsafe fn alloc_zeroed(&self, layout: Layout) -> *mut u8 { ... }
  unsafe fn realloc(
        &self, ptr: *mut u8, layout: Layout, new_size: usize) -> *mut u8 { ... }
}
```

為我們的空殼實作 `GlobalAlloc`，trait 本身就是 unsafe 還真鮮；
Layout 是 rust 定義用來表示一塊記憶體的資料結構，儲存了這塊記憶體的 size, align 等資訊，有趣的是，rust dealloc 的時候也會帶 layout 進來，
這意味著跟 C 的 free 不一樣， `GlobalAlloc` 在背後還是有某種管理機制在 realloc 的時候可以知道記憶體的尺寸資訊：  
```rust
use core::ptr::null_mut;

unsafe impl {
  unsafe fn alloc(&self, _layout: Layout) -> *mut u8 {
    null_mut()
  }   

  unsafe fn dealloc(&self, _ptr: *mut u8, _layout: Layout) {
    panic!("dealloc should be never called");
  }   
}
```

除了這個還要加上 memory alloc error 的實作，或者在 main.rs (lib.rs) 裡面加上
`#![feature(default_alloc_error_handler)]` 讓編譯器自行弄成 `panic!`。
```rust
#[alloc_error_handler]
fn alloc_error_handler(layout: Layout) -> ! {
  panic!("allocation error {:?}", layout);
}
```

最後是在 `main.rs` 將我們的空殼 `HeapAllocator` 設定為 `#[global_allocator]`。
```rust
#[global_allocator]
static ALLOCATOR: HeapAllocator = HeapAllocator;
```

如此一來上面使用 `Box` 的程式就能通過編譯了；在執行時則會 panic，因為 Box 會對 alloc 傳回的 null pointer 存取。

# 實作 Linked List

一般最簡便的 heap 管理就是用 linked_list，這次也好好跟 linked_list_allocator 的作者學會怎麼打造 rust 的 linked_list。  
第一步先打造我們的 `Hole`，用 Option 來打造 list 應該是基本中的基本，Option 內是另一個 Hole 的 static reference。

```rust
pub struct Hole {
  size: usize,
  next: Option<&'static mut Hole>,
}
```

`HoleList` 的 first 是 dummy Hole，size 為 0；在生成的時候會如下，在 hole_addr 上建一個 Hole pointer，對 pointer 寫入 Hole struct 即可。  
ptr 寫入這個動作是 unsafe 的，不過我們整個 new 函式都是 unsafe 所以沒問題。

```rust
pub struct HoleList {
  first: Hole,
}

impl HoleList {
  pub unsafe fn new(hole_addr: usize, hole_size: usize) -> Self {
    let ptr = hole_addr as *mut Hole;
    ptr.write( Hole {
      size: hole_size,
      next: None,
    });
    Self {
      first: Hole {
        size: 0,
        next: Some(&mut *ptr),
      }
    }
  }
}
```

因為 `Hole` 本身有 reference 不適合複製，另外實作一個 `HoleInfo` 來代表一塊記憶體：

```rust
struct HoleInfo {
  addr: usize,
  size: usize,
}

impl Hole {
  pub fn info(&self) -> HoleInfo {
    HoleInfo {
      addr: self as *const _ as usize,
      size: self.size,
    }
  }
}
```

在 `HoleList` 之外我們再包一層 `Heap` 用來記錄整個記憶體使用的狀況：

```rust
struct Heap {
  bottom: usize,
  size: usize,
  used: usize,
  holes: HoleList,
}

impl Heap {
  pub const fn empty() -> Self {
    Self {
      bottom: 0,
      size: 0,
      used: 0,
      holes: HoleList::empty(),
    }
  }
}
```

原本空無一物的 `HeapAllocator` 也要改造一番，為了避免 malloc 的競態條件，heap 外要加上 Mutex。
```rust
pub struct HeapAllocator {
  heap: Mutex<Heap>,
}

impl HeapAllocator {
  pub const fn empty() -> Self {
    Self {
      heap: Mutex::new(Heap::empty()),
    }
  }
}
```

整體的架構依序為：`HeapAllocator` -> `Heap` -> `HoleList` -> `[Hole]`

# 實作 alloc

global allocate 函式，實作很單純，因為我們已經知道不會有記憶體被 free，要做的就只有拿出下一個元素（單一區塊管理所有記憶體），
檢查 size 夠不夠，如果夠的話就在 `Hole` 的尾端把空出記憶體；不夠的話就是回傳 `Err`。  
實際的 linked_list 則是在 `Hole` 沒有足夠記憶體的時候，會去拿出下一個 `Hole` 試著 alloc 看看，直到 list 尾端就回傳 `Err`；
`Allocation` 用來表示一塊分配的記憶體，未來處理 align 的時候會在裡面加上更多東西。

```rust
pub fn allocate(previous: &mut Hole, layout: Layout) -> Result<Allocation, ()> {
  let mut current = previous.next.as_mut().unwrap().info();
  let required_size = layout.size();
  if current.size < required_size {
    Err(())
  } else {
    let allocated_info = HoleInfo {
      addr: current.addr + current.size - required_size,
      size: required_size,
    };
    current.size -= required_size;
    Ok(Allocation {
      info: allocated_info,
    })
  }
}
```

如此一來，`HoleList` 就是把自己的 List 拿出來，呼叫 global allocate 函式得到 `Allocation`，轉型為 [NonNull pointer](https://doc.rust-lang.org/std/ptr/struct.NonNull.html) ，
這裡可以用 NonNull 因為 Null 的狀況已經由 Result Err 來表示了：

```rust
// HoleList
pub fn allocate(&mut self, layout: Layout) -> Result<NonNull<u8>, ()> {
  allocate(&mut self.first, layout).map(|allocation| {
    NonNull::new(allocation.info.addr as *mut u8).unwrap()
  })
}
```

在實作 `GlobalAlloc` 的 alloc 函式裡面呼叫 allocate，如果是 `Err` 的狀況會由 map_or 轉型為 Null pointer。
```rust
unsafe impl GlobalAlloc for HeapAllocator {
  unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
    self.heap
      .lock()
      .allocate(layout)
      .map_or(null_mut(), |allocation| allocation.as_ptr())
  }
}
```

# 初始化 Heap

我們 heap 的尺寸和 xv6 一樣設定為 128MB（扣掉 kernel code 的空間，因此實際空間會略小於 128MB），heap 的起始位置則由 linker script 決定，在 linker script .data, .bss 等區間之後，加上：
```txt
PROVIDE(_END = .);
```

初始化記憶體就能透過 `extern "C"` 取得 `_END` 的值，再把這個 heap 設定寫入 ALLOCATOR 的 heap 中。

```rust
pub fn init_heap() {
  extern "C" {
    static _END: usize;
  }

  let heap_start: usize = unsafe {
    &_END as *const usize as usize
  };
  let heap_end = memorylayout::PHYSTOP as usize;
  let heap_size = heap_end - heap_start;
  unsafe {
    ALLOCATOR
      .heap
      .lock()
      .init(heap_start, heap_size)
  }
}
```

# 結語
我們實作了一款只會 allocate 不會 free 的 allocator，但至少，現在我們可以在 code 裡面使用各種使用 heap 的資料結構，例如上述的 Box。  
簡而言之我們的 HeapAllocator 大概可以用下面這段概述：

> 我之前是幫人弄記憶體管理的，而我 malloc 的原則是：「○林涼 malloc 爆」  
> 沒錯，就是○林涼 malloc 爆，老子才不管甚麼要不要 free 的，每次 malloc 就是一大塊。1K malloc 1M，1M malloc 1G。  
> 後來作業系統跳 panic 跟我說記憶體不足，你有頭緒嗎？  
> 我TMD怎麼會知道。

第二，如果你跟 xv6 的實作比較的話，可以明顯看到 rust 優於 C 的一點，rust 的 locking 是強制性的，只要我們把東西包到 Mutex 裡面，
你一定要用 lock 再去存取內部的資料；相對的 xv6 實作則是：
```c
struct {
  struct spinlock lock;
  struct run *freelist;
} kmem;
```
存取 freelist 之前記得先跟 lock 去 acquire lock。  
啊沒有 lock 會怎麼樣？系統爆掉啊。  
誰的錯？當然是程式設計師的。  

Rust 在這方面 *比較* 貼心一點，雖然 Mutex 的實作相對麻煩一些，但只要做完，實作的限制就會如通往建功嶼的海中道路般浮現；
你的實作會被限制到只剩安全的方式，不這麼做 compiler 就會跳出來把你攔住，~~叫你回去修練 21 小時之後再來~~，
或是非得讓你狂下 unsafe 或 unwrap 弄出有危險的程式它才放行。

套句 jserv 教授的話：  
> C 語言假定了程式設計師都是聰明人，很清楚知道自己在做什麼

而愚者用了 C 就必須要為自己的愚蠢付出代價。
