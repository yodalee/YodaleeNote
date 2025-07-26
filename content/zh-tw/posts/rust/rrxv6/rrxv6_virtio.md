---
title: "rrxv6 : virtio"
date: 2023-05-04
categories:
- rust
- operating system
tags:
- virtio
- rust
- xv6
- riscv
series:
- rrxv6
forkme: rrxv6
---

在去年五月[上一回的文章]({{< relref "rrxv6_user_mode" >}})中，我們做到了 OS 版的 hello world，
讓 user process 呼叫 print 的 syscall，並由 OS 處理該 syscall 印出 hello world。  
在這之後我花了一段時間（好長的一段）思考到底要做什麼，後面 xv6 依序初始化的東西包括幾個：
1. buffer cache
2. inode table
3. file table
4. virtio
5. 做更多 user process 相關的部分

後來發現 1,2,3 都相依於 4，沒有 virtio 讀不了磁碟那還管什麼 file, inode；
User process 在沒有 4 的狀況下，寫起來也是綁手綁腳，於是就決定先挑戰 qemu 的 virtio。
<!--more-->

結果這一拖竟然就快一年了，一個原因是 virtio 比較太複雜了，又被 rust 的語言檢查一直卡，然後又遇到一卡車的事。  
* 6-8 月忙著準備 COSCUP 還有搬家
* 8-9 月參加 COSCUP 跟 FLOLAC，這段時間有認真開發一下，大部分的 virtio 模組也是那時候寫好了，但就缺臨門一腳。
* 10-4 月因為換工作，加上花了大約半年重新熟習 verilog，寫了 [RSA256](https://github.com/yodalee/rsa256) 這個專案，
結果到現在才重回這個放置許久的 project。

不說廢話，讓我們進到 virtio 的世界吧。

# Virtio

Virtio 設定一組溝通的標準，virtual machine 依此標準跟 hypervisor 溝通；
hypervisor 則依此標準實作不同的 I/O 裝置；透過這層介面提升模擬程式的執行效率。  
更詳細的介紹有點費唇舌，找了一篇不錯的資源當參考資料，大家可以看一下：
* [Virtio 半虛擬化驅動](https://godleon.github.io/blog/KVM/KVM-Paravirtualization-Drivers/)

在寫程式碼的參考上，肯定沒有任何說明比 [官方文件](https://docs.oasis-open.org/virtio/virtio/v1.2/virtio-v1.2.html)
更權威了，文件大量規範實作 Virtio 的雙方：Virtual Machine 的 *Driver* 和 Hypervisor 的 *Device* 有什麼要求，
下面文章中會大量引用這個網頁的內容，就請大家多多翻閱。

在 qemu 要開啟 virtio 介面時指令如下：
```bash
qemu-system-riscv64 -machine virt -bios none -m 128M -smp 1 -nographic \
  -global virtio-mmio.force-legacy=false \
  -drive file=fs.img,if=none,format=raw,id=x0 \
  -device virtio-blk-device,drive=x0,bus=virtio-mmio-bus.0 \
  -kernel target/riscv64imac-unknown-none-elf/debug/rrxv6
```

* virtio-mmio.force-legacy = false：設定 virtio-mmio 不強制使用舊版本(legacy version)。
* 使用映像檔 `fs.img`，格式為 raw，ID 為 x0，fs.img 我是先從 xv6 複製過來，等未來 user 程式完備之後再自己生。
* 虛擬磁碟裝置為 virtio-blk-device，連接先前 ID 為 x0 的映像檔，並接在 virtio-mmio-bus.0 上

# Virtio 結構

在 virtio 結構上寫得最好的是 redhat 的文件
* [Virtqueues and virtio ring: How the data travels](https://www.redhat.com/en/blog/virtqueues-and-virtio-ring-how-data-travels)
* [Virtio devices and drivers overview: The headjack and the phone](https://www.redhat.com/en/blog/virtio-devices-and-drivers-overview-headjack-and-phone)

virtio 的設備至少有下列的介面：
* [Device status field](https://docs.oasis-open.org/virtio/virtio/v1.2/cs01/virtio-v1.2-cs01.html#x1-110001)：
現在 device 的狀態
* [Feature bits](https://docs.oasis-open.org/virtio/virtio/v1.2/cs01/virtio-v1.2-cs01.html#x1-140002)：
設備透過 feature bits 告訴 driver 自己提供哪些特性（用功能也許比較妥當），
driver 則會在初始化時設定 feature bits 告訴設備我要使用哪些特性。
* [Notifications](https://docs.oasis-open.org/virtio/virtio/v1.2/cs01/virtio-v1.2-cs01.html#x1-180003)：
讓 device 和 driver 互相溝通的介面
* [Zero or more virtqueues](https://docs.oasis-open.org/virtio/virtio/v1.2/cs01/virtio-v1.2-cs01.html#x1-270006)：
virtio queue 是 virtio 用來傳輸大量資料的機制，底層有兩列 Available Buffer 跟 Used Buffer
  * Driver 把 Available buffer 加到 queue 裡，然後通知 device 處理
  * Device 處理完 buffer 之後，把 buffer 加到 Used Buffer 中，通知 driver 處理完成。

在這個架構上，virtio 支援多達 [40 多種不同的設備](https://docs.oasis-open.org/virtio/virtio/v1.2/cs01/virtio-v1.2-cs01.html#x1-2160005)。  
我想是因為大家都沒寫過多少不同的裝置，頂多寫個 block device，參考資料都只說 block device 用一個 queue，
net device 傳輸跟接收用兩個。  
不過如果我們仔細看官方文件，會在 [2.7.12 Virtqueue Operation](https://docs.oasis-open.org/virtio/virtio/v1.2/cs01/virtio-v1.2-cs01.html#x1-6300012) 找到下列文字：

> the simplest virtio network device has two virtqueues: the transmit virtqueue and the receive virtqueue.

好吧我們知道第一個是誰這樣寫的了 (._.)

# Virtio Initialization

了解到這樣可以開始寫 code 了，因為 virtio 本身很獨立，全部放在 virtio 資料夾裡。  
從 virtio 的 header 開始，結構大量參考 r-core 出的 [virtio-driver](https://github.com/rcore-os/virtio-drivers)，設計上極為相近，幾乎到了抄襲的地步了。

## Header Layout

Header Layout 參見 [4.2.2 MMIO Device Register Layout](https://docs.oasis-open.org/virtio/virtio/v1.2/cs01/virtio-v1.2-cs01.html#x1-1670002)，
如果使用 legacy interface 則是 [4.2.4 Legacy Interface](https://docs.oasis-open.org/virtio/virtio/v1.2/cs01/virtio-v1.2-cs01.html#x1-1770004)。

```rust
use volatile_register::{RO, RW, WO};

pub struct VirtioHeader {
  // 0x00
  magic: RO<u32>,
  version: RO<u32>,
  device_id: RO<u32>,
  vendor_id: RO<u32>,
  // 0x10
  device_features: RO<u32>,
  device_features_sel: WO<u32>,
  _r0: [u32; 2],
  // 0x20
  driver_features: WO<u32>,
  driver_features_sel: WO<u32>,
  _r1: [u32; 2],
  // 0x30
  queue_sel: WO<u32>,
  queue_num_max: RO<u32>,
  queue_num: WO<u32>,
  _r2: [u32; 1],
  // 0x40
  _r3: [u32; 1],
  queue_ready: RW<u32>,
  _r4: [u32; 2],
  // 0x50
  queue_notify: WO<u32>,
  _r5: [u32; 3],
  // 0x60
  interrupt_status: RO<u32>,
  interrupt_ack: WO<u32>,
  _r6: [u32; 2],
  // 0x70
  status: RW<DeviceStatus>,
  _r7: [u32; 3],
  // 0x80
  queue_desc_low: WO<u32>,
  queue_desc_high: WO<u32>,
  _r8: [u32; 2],
  // 0x90
  queue_driver_low: WO<u32>,
  queue_driver_high: WO<u32>,
  _r9: [u32; 2],
  // 0xa0
  queue_device_low: WO<u32>,
  queue_device_high: WO<u32>,
  _r10: [u32; 21],
  // 0xfc
  config_generation: RO<u32>,
}
```

MMIO 變數會從記憶體直接映射在 device 上，用 [volatile_register](https://docs.rs/volatile-register/latest/volatile_register/) 來讀寫，magic value, version, device_id, vendor_id 依序是以下的值：
* magic value = 0x74726976 ASCII "virt"
* version = 2 (如果是 legacy device 會是 1)
* device_id: [Block device](https://docs.oasis-open.org/virtio/virtio/v1.2/cs01/virtio-v1.2-cs01.html#x1-2160005) = 2
* vendor_id = 0x554D4551 ASCII "QEMU" 倒過來寫，這可能是某種工程師的冷笑話…

據此我們可以實作 VirtioHeader 的 new 函式，從 u64 address 轉成 VirtioHeader Pointer，檢查 register 通過把 reference 丟出去，檢查不過就會拋出 error

```rust
impl VirtioHeader {
  pub fn new<'a>(addr: u64) -> Result<&'a mut VirtioHeader, Error> {
    let header = unsafe { &mut *(addr as *mut VirtioHeader) };
    match header.verify() {
      true => Ok(header),
      false => Err(Error::HeaderInitError),
    }
  }

  pub fn verify(&self) -> bool {
    self.magic.read() == 0x74726976
      && self.version.read() == 2
      && self.device_id.read() == 2
      && self.vendor_id.read() == 0x554D4551
  }
}
```

## Driver Initialization

當使用者初始化一個裝置的時候，Driver 要實作的流程寫在 [3.1.1 Driver Initialization](https://docs.oasis-open.org/virtio/virtio/v1.2/cs01/virtio-v1.2-cs01.html#x1-1070001)，
步驟如下：
1. 對 status 寫入 0 重設裝置
2. 設定 status ACKNOWLEDGE bit
3. 設定 status DRIVER bit
4. 讀取 feature bits，並寫入該設定的子集
5. 設定 status FEATURES_OK bit，完成功能設定
6. 讀取 status 確定 FEATURES_OK 已設定，否則表示 device 無法使用
7. 其他設定如設定 queue
8. 設定 status DRIVER_OK bits，完成設定。

status bits 定義在 [2.1 Device Status Field](https://docs.oasis-open.org/virtio/virtio/v1.2/cs01/virtio-v1.2-cs01.html#x1-110001)，
我們可以輕鬆用 [bitflags](https://docs.rs/bitflags/latest/bitflags/) 給予 bit 有意義的名稱。

```rust
bitflags! {
  pub struct DeviceStatus: u32 {
    const ACKNOWLEDGE = 1;
    const DRIVER = 2;
    const DRIVER_OK = 4;
    const FEATURES_OK = 8;
    const DEVICE_NEEDS_RESET = 64;
    const FAILED = 128;
  }
}
```

如此一來 header 就能實作兩個初始化的函式，在 begin_init/end_init 中間，
也就是設定 DRIVER_OK 前，使用者可以去設定 virtio queue：
```rust
pub fn begin_init(&mut self, negotiate_features: impl FnOnce(u64) -> u64) -> Result<(), Error> {
  unsafe {
    self.status.write(DeviceStatus::ACKNOWLEDGE);
    self.status.write(DeviceStatus::DRIVER);
    let features = self.read_device_features();
    self.write_driver_features(negotiate_features(features));
    self.status.write(DeviceStatus::FEATURES_OK);
    // check that status keep in FEATURES_OK
    if self.status.read() != DeviceStatus::FEATURES_OK {
      return Err(Error::HeaderInitError);
    }
  }
  Ok(())
}

pub fn end_init(&mut self) {
  unsafe {
    let mut status = self.status.read();
    status |= DeviceStatus::DRIVER_OK;
    self.status.write(status);
  }
}
```

# Virtio Block

有了 header ，先跳過 VirtioQueue 的部分看看怎麼用它，我們的目標是給 rrxv6 用而不是 general driver，
所以只實作 Block Device：

```rust
pub struct VirtioBlock {
  pub header: &'static mut VirtioHeader,
  queue: VirtioQueue,
}

impl VirtioBlock {
  pub fn new(header: &'static mut VirtioHeader) -> Result<Self, Error> {
    header.begin_init(|features| {
      let features = BlockFeatures::from_bits_truncate(features);
      let disable_features = BlockFeatures::RO
            | BlockFeatures::CONFIG_WCE
            | BlockFeatures::RING_EVENT_IDX
            | BlockFeatures::RING_INDIRECT_DESC;
        (features - disable_features).bits()
    })?;

    let queue = VirtioQueue::new(header, 0, 8)?;
    header.end_init();

    Ok(Self { header, queue })
  }
}
```

## 初始化 device

實作的介面是 MMIO，在記憶體上會有一堆對應的位址會映射到 virtio device 上， 在 [qemu riscv virt 裝置](https://github.com/qemu/qemu/blob/master/hw/riscv/virt.c#L90)
上這個位置是在 0x1000_1000，大小 0x1000。

`memorylayout.rs` 裡面宣告 VRITIO0 和 VIRTIO_IRQ
```rust
pub const VIRTIO0 : u64 = 0x1000_1000;
pub const VIRTIO0_IRQ : u64 = 1;
```

[kvm.rs 的部分]({{< relref "rrxv6_virtual_memory" >}})也要記得處理好存取權限，否則 header 一取存就會觸發記憶體保護：
```rust
kvmmap(VirtAddr::new(VIRTIO0), PhysAddr::new(VIRTIO0), PAGESIZE,
        PteFlag::PTE_READ | PteFlag::PTE_WRITE);
```

初始化 header，再丟給 `VirtioBlock` 初始化 Block device，在主程式依照慣例，使用 `Mutex<Option<T>>` 儲存 global 變數：

```rust
// disk.rs
static mut DISK: Mutex<Option<VirtioBlock>> = Mutex::new(None);

pub fn init_disk() {
  let header = VirtioHeader::new(VIRTIO0).expect("Error: Disk header initialization");
  let block = VirtioBlock::new(header).expect("Error: Disk initialization");
  unsafe {
    let mut disk = DISK.lock();
    *disk = Some(block);
  }
}
```

# Virtio Queue

queue 的結構可看  [2.6 Virtqueues](https://docs.oasis-open.org/virtio/virtio/v1.2/cs01/virtio-v1.2-cs01.html#x1-270006)。
一個 queue 會有下面三個部分：
1. Descriptor Area: 用來描述 buffer 的內容，格式定義 [2.7.5 The Virtqueue Descriptor Table
](https://docs.oasis-open.org/virtio/virtio/v1.2/cs01/virtio-v1.2-cs01.html#x1-430005)
2. Available Ring 或稱 Driver Area: 從 Driver 送到 Device 的其他資料，格式定義 [2.7.6 The Virtqueue Avgailable Ring](https://docs.oasis-open.org/virtio/virtio/v1.2/cs01/virtio-v1.2-cs01.html#x1-490006)
3. Used Ring 或稱 Device Area: 從 Device 送到 Driver 的其他資料，格式定義 [2.7.8 The Virtqueue Used Ring](https://docs.oasis-open.org/virtio/virtio/v1.2/cs01/virtio-v1.2-cs01.html#x1-540008)

後兩者我個人是比較習慣 Available Ring 跟 Used Ring 的叫法，不過注意在 [MMIO register](https://docs.oasis-open.org/virtio/virtio/v1.2/cs01/virtio-v1.2-cs01.html#x1-1670002)
有四個 register 是用 driver 跟 device 來稱呼，包括 QueueDriverLow/High, QueueDeviceLow/High。  
跟 header 一樣，我們可以用 struct 和 bitflag 構成 Descriptor, AvailRing, UsedRing 等結構和它們的 flag。

```rust
pub struct Descriptor {
  /// Address
  pub addr: u64,
  /// Length
  pub len: u32,
  /// The flags
  pub flags: DescriptorFlag,
  /// Next field if flags & NEXT
  pub next: u16,
}

bitflags! {
  pub struct DescriptorFlag: u16 {
    /// Marks a buffer as continuing via the next field.
    const NEXT = 1;
    /// Marks a buffer as device write-only.
    const WRITE = 2;
    /// The buffer contains a list of buffer descriptors.
    const INDIRECT = 4;
  }
}

// FIXME: expose interface instead of public access
pub struct AvailRing {
  pub flags: AvailRingFlag,
  pub idx: u16,
  pub ring: [u16; 32],
  pub used_event: u16,
}

bitflags! {
  pub struct AvailRingFlag: u16 {
    const NO_INTERRUPT = 1;
  }
}
```

## Queue Initialization

初始化 queue 的步驟描述在 [4.2.3 MMIO-specific Initialization And Device Operation](https://docs.oasis-open.org/virtio/virtio/v1.2/cs01/virtio-v1.2-cs01.html#x1-1700003)：
1. 選定要設定的 queue id，寫入 register QueueSel
2. 確認 QueueReady 讀到 0，表示 Queue 沒在使用中
3. 讀取 QueueNumMax，讀到 0 表示 Queue 無法使用
4. 分配 queue 使用的**連續**記憶體
5. 對 QueueNum 寫入 queue size
6. 對將分配好的 Descriptor, Available Ring, Used Ring 的位址寫入 header 對應的 register QueueDescLow/Hight, QueueDriverLow/High, QueueDeviceLow/High
7. 對 QueueReady 寫入 1。

實作 struct VirtioQueue：

```rust
pub struct VirtioQueue {
  /// index of the queue
  idx: u32,
  /// size of the queue
  size: u16,
  /// address of descriptor
  pub desc: NonNull<Descriptor>,
  /// address of available ring
  pub avail: NonNull<AvailRing>,
  /// address of used ring
  used: NonNull<UsedRing>,
}
```

在 new 的時候會呼叫 kalloc 分配 desc, avail, used 三塊記憶體，透過 header 的函式寫入 register 中：

```rust
impl VirtioQueue {
  pub fn new(header: &mut VirtioHeader, idx: u32, size: u16) -> Result<Self, Error> {
    // …
    // allocate and zero queue memory.
    // note that kalloc will fill memory with 0 for us
    let desc = NonNull::new(kalloc() as *mut _).ok_or(Error::NoMemory)?;
    let avail = NonNull::new(kalloc() as *mut _).ok_or(Error::NoMemory)?;
    let used = NonNull::new(kalloc() as *mut _).ok_or(Error::NoMemory)?;

    // write physical address
    header.set_queue(
      idx,
      size,
      desc.addr().get() as u64,
      avail.addr().get() as u64,
      used.addr().get() as u64,
    );

    header.set_queue_ready(/*ready=*/ true);
    // …
  }
}
```

# Virtio Interrupt

在設定好 queue 和 block device 之後，就可以來試著發 request 給 device 了，這篇礙於篇幅我們就先不真的讀寫 device，
而是先讓 device 發一個 interrupt 給我就可以了。  
首先在 [plic 的部分]({{< relref "rrxv6_interrupt" >}})，設定 virtio 的 interrupt 可以發生，
並在 trap 函式 `handle_external_interrupt` 函式遇到 VIRTIO0_IRQ 時直接讓 kernel panic。

在 disk.rs 實作一個 read_disk 函式：

```rust
pub fn read_disk() {
  let mut disk = unsafe { DISK.lock() };

  let request = BlockRequest {
    typ: RequestType::In,
    reserved: 0,
    sector: 0,
  };

  let block = disk.as_mut().unwrap();
  let mut descriptor = unsafe { block.queue.desc.as_mut() };
  let mut available = unsafe { block.queue.avail.as_mut() };

  // setup block request
  descriptor.addr = &request as *const _ as u64;
  descriptor.len = size_of::<BlockRequest>() as u32;
  descriptor.flags = DescriptorFlag::NEXT;
  descriptor.next = 0;

  available.idx += 1;
  sync_synchronize();

  block.header.set_queue_notify(0);
}
```

BlockRequest 的詳細設計下一章鐵定還會大改，這裡的參考來自 [5.2.6 Device Operation](https://docs.oasis-open.org/virtio/virtio/v1.2/cs01/virtio-v1.2-cs01.html#x1-2850006)，
我們這邊只送 Type = In -> Read，讀第零個 sector，也就是 0-512 bytes 的資料。  
接著把 request 塞進第一個 descriptor 裡面，填入位址跟長度；故意把 descriptor 下一個 descriptor 設定為自己。  
發出 request 的方法為修改 available ring 的 idx，並對 header 的 QueueNotify 寫入有需求的 queue id，第一個 virtio request 就完成了。

在執行的時候，會看到下列的輸出：

```txt
qemu-system-riscv64 -machine virt -bios none -m 128M -smp 1 -nographic 
  -global virtio-mmio.force-legacy=false -drive file=fs.img,if=none,format=raw,id=x0 
  -device virtio-blk-device,drive=x0,bus=virtio-mmio-bus.0 
  -kernel target/riscv64imac-unknown-none-elf/debug/rrxv6
rrxv6 start
qemu-system-riscv64: Looped descriptor
panicked at 'VIRTIO IRQ', src/trap.rs:103:13
```

第一句來自 qemu，因為我們故意把 descriptor 的 next 指向自己，造成 qemu 在 virtio.c 裡拋出循環 descriptor 錯誤。  
qemu 檢出 looped descriptor 放棄處理，會對我們的 OS 發出一個中斷，
被 interrupt handler 收下來之後，由 OS 呼叫 panic! 讓核心當掉。

# 結語

雖然是個不完整的演示，但這章展示我們成功連接 qemu 的 virtio device，並且發出一個有錯誤的 read operation，讓 qemu 發出一個 virtio 中斷。  
之所以沒有實作完整的 read operation，是因為這樣會需要多個 Descriptor，
但 queue.rs 的 Descriptor 型態目前是 `NonNull<Descriptor>`；如果要存取多個 Descriptor 就需要改變型態為 `[Descriptor;SIZE]`，這在 rust 是 [fat pointer](https://stackoverflow.com/questions/57754901/what-is-a-fat-pointer) 和 NonNull 不相容。

接下來會想辦法解決這個問題，下一章目標就是發出完整的 request 並讀取到磁碟的內容了。