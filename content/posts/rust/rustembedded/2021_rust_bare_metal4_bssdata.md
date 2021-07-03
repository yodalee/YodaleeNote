---
title: "在 2021 年要如何開發 Rust 裸機程式：.bss 和 .data"
date: 2021-06-22
categories:
- rust
- embedded system
tags:
- rust
- embedded system
series:
- rust bare-metal programming
---

現在的 main 程式現在只能使用 stack variable，還不能使用 static 變數，因為我們在 linker 內只放了 .text 區段，
[static 變數](https://blog.gtwang.org/programming/memory-layout-of-c-program/)
所用的 .data（已初始化）、.bss（未初始化） 都還沒準備。

<!--more-->

## .data .bss

讓我們補上這塊，首先是 .rodata .bss .data 區段，在 linker script 裡面加上這些區段：
```txt
.rodata :
{
  *(.rodata .rodata.*);
} > FLASH

.bss :
{
  *(.bss .bss.*);
} > RAM

.data :
{
  *(.data .data.*);
} > RAM
```

用 rust 裡面*很不受歡迎的 global 變數*來生成 DATA BSS 區段的資料；
RODATA 區段可以用 static array 或像這樣用 const 來產生；在 main 裡面一定要 reference 它們，不然 linker 就會很高興的把它們移除掉。  
另外在 rust 裡面對 static mut 取 reference 是 unsafe behavior，因為 static 有可能被多個報行緒共享。

```rust
const RODATA2: &[u8] = b"hello";
static mut BSS: u8 = 0;
static mut DATA: u32 = 0x5a5aa5a5;

#[no_mangle]
pub fn main() -> ! {
  let _x = RODATA;
  let _y = unsafe { &BSS };
  let _z = unsafe { &DATA };
  loop {}
}
```

### 編譯

編譯完之後，用 objdump 檢視編譯出來的執行檔，可以在裡面找到 .data 區段：
```txt
$ arm-none-eabi-objdump -s  target/thumbv7m-none-eabi/debug/app -j .data
Contents of section .data:
 20000004 a5a55a5a
```

編譯器並沒有輸出 .bss 區段的資料，或說 objdump 不會顯示 .bss 區段的資料（雖然我不知道為什麼），但是 .bss 其實是存在的，
上面的 linker script 指定 RAM 裡面依序放著 .bss 跟 .data 區段，因此 RAM 開始的 0x2000_0000 就放著 .bss，
0x2000_0004 則放著 0x5a5aa5a5 的 .data 區段。

## LMA 與 VMA

讓我們把執行檔轉成要燒錄到硬體上的二進位檔：
```txt
$ arm-none-eabi-objcopy -O binary target/thumbv7m-none-eabi/debug/app bin

$ ls -l bin
513M  6月 22 12:09 bin
```
這個尺寸竟然**高達 513 MB**。

原因是我們指定了 .data 區段從 RAM 開始，而目標機器的 RAM 位址是 0x20000000 ，也就是 512MB 的地方開始，
放上 .bss 跟 .data 的資料後結束，於是 objcopy 就產生了一個 513MB 的二進位檔出來。  
但這個二進位檔是沒意義的，燒錄的時候只有燒進 flash 裡面才有用，RAM 裡的在斷電時資料就消失了。

現下這段 code 在 qemu 能夠正確執行（可能因為 qemu 會拿著 binary 塞進虛擬的 RAM 裡面，並沒有模擬斷電資料未初始化的情形），
在實際的硬體上，讀取 static 變數會得到一堆亂數。
再次修改 linker script，在 bss data 區段開始跟結束提供符號，並且利用 AT 設定 .data 的 [LMA](https://blog.louie.lu/2016/11/06/10%E5%88%86%E9%90%98%E8%AE%80%E6%87%82-linker-scripts/)：

```
.bss :
{
  _sbss = .;
  *(.bss .bss.*);
  _ebss = .;
} > RAM

.data AT(ADDR(.rodata) + sizeof(.rodata)):
{
  _sdata = .;
  *(.data .data.*);
  _edata = .;
} > RAM

_sidata = LOADADDR(.data);
```

修改如下：
* _sbss, _ebss, _sdata, _edata 符號標示 bss 跟 data 的開始與結束
* .data 用 AT 設定 LMA，排在 .rodata 之後
* _sidata 符號使用 LOADADDR 取得 .data 的 LMA，_sdata, _edata 取得的則是 VMA。

編譯後，這次用 objcopy 產生的燒錄檔的尺寸就正常多了，只需要 161 bytes。
用 `objdump -h` 也能看到 .data 的 LMA 與 VMA 確實被分開了：
```txt
$ arm-none-eabi-objdump -h target/thumbv7m-none-eabi/debug/app
Sections:
Idx Name          Size      VMA       LMA       File off  Algn
...
  4 .data         00000004  20000004  0000009d  00020004  2**2
                  CONTENTS, ALLOC, LOAD, DATA
```

在我們 .rodata (Hello World 之後) 也能看到 0x5a5aa5a5 的 .data 區段，也就是說 .data 的初始資料已經包含到二進位燒錄檔內，
在燒錄進 flash 的時候，就會把這個初始值跟著燒進 flash。

```txt
$ arm-none-eabi-objcopy -O binary target/thumbv7m-none-eabi/debug/app bin
$ xxd bin
00000080: fede ffe7 fee7 0000 4865 6c6c 6f00 0000  ........Hello...
00000090: 8800 0000 0500 0000 576f 726c 64a5 a55a  ........World..Z
000000a0: 5a                                       Z
```

光這樣是不夠的，我們還需要在程式啟動，進到 main 之前，把這些值得 flash 複製到 RAM 裡面才行。  
在 reset_handler 呼叫 main 之前加入這段 code，使用 `core::ptr` 的 write_bytes 初始化 bss 區段為 0 ，
用 copy_nonoverlapping 將資料從 flash 複製到 RAM 裡面：

```rust
extern "C" {
  static mut _sbss: u8;
  static mut _ebss: u8;

  static mut _sdata: u8;
  static mut _edata: u8;
  static _sidata: u8;
}

let count = &_ebss as *const u8 as usize - &_sbss as *const u8 as usize;
ptr::write_bytes(&mut _sbss as *mut u8, 0, count);

let count = &_edata as *const u8 as usize - &_sdata as *const u8 as usize;
ptr::copy_nonoverlapping(&_sidata as *const u8, &mut _sdata as *mut u8, count);

// call main
```

這樣程式在硬體上就能正常運作了。

## 其他
我注意到在 RODATA，要產生 RODATA 有下列兩種寫法：
```rust
static STATIC_RO: &[u8] = "Hello";
const CONST_RO: &[u8] = "World";
```

兩種寫法會產生兩種不同的 .rodata：
第一種寫法，會產生三個部分：資料本體、u32 資料起始位址、u32 資料長度。
第二種寫法，只會產生資料本體。

以我上面為例，編譯出來的 .rodata 會是：
```txt
$ arm-none-eabi-objdump -s  target/thumbv7m-none-eabi/debug/app -j .rodata

Contents of section .rodata:
 0088 48656c6c 6f000000 88000000 05000000  Hello...........
 0098 576f726c 64                          World    
```

`Hello` 之後 0x88 為起始位址，0x5 是長度；`World` 則是以單純的資料存在。
我是不清楚 static 跟 const 在 rust 裡面最後怎麼轉成物件檔的資料區段，看起來用 const 比用 static 還要節省一咪咪的空間，
但為什麼會有這個差異我就不懂了，希望有了解的大大可以為小弟指點一下迷津。