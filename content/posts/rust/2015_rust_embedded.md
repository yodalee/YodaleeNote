---
title: "使用 rust 來寫極簡的嵌入式系統"
date: 2015-05-06
categories:
- embedded system
- rust
tags:
- embedded system
- rust
series: null
---

最近看到一些有趣的東西：  
* [rust_arm_cortex-m_semihosted_hello_world](https://github.com/llxwj/rust_arm_cortex-m_semihosted_hello_world)  
* [armboot](https://github.com/neykov/armboot)  

用rust 來寫嵌入式系統，感覺相當生猛，正好最近在上傳說中的jserv 大神的嵌入式系統，就想把嵌入式系統作業用到東西，用rust 實作出來，
主要參考的內容包括上面的armboot，跟作業的[mini-arm-os](https://github.com/embedded2015/mini-arm-os):  

本篇相關的[原始碼](https://github.com/yodalee/rust-mini-arm-os)：  
<!--more-->

跟armboot 類似，我用了libarm/stm32f4xx.rs(變體)跟 `zero/std_types` 這兩個lib，不使用rust std的lib：   
```rust
mod zero {
    pub mod std_types;
    pub mod zero;
}
#[macro_use]
mod libarm {
#[macro_use]
pub mod stm32f1xx;
}
```
zero比較簡單，定義一些C 裡面用到的型態應該對應到rust 什麼型態，和rust 基本的trait 如Sized, Copy 等等，不寫的話rustc 會抱怨找不到這些trait；
就像在rust\_hello\_world這個實作裡面，也是把這些trait 寫在main裡面，我猜這些內容和Rust 的基本設計有關，目前還不是很清楚。   

libarm就比較複雜，這感覺像是作者自己寫的，針對的是stm32f4, arm-cortex m4 的硬體。  
理論上這裡應該是先研究stm32f4要怎麼初始化，不過我偷懶，先直接把部分的stm32f4 硬體位址修改成stm32f1 的，這樣舊的code 就可以直接搬過來XD。   

Stm32f4xx.rs的內容，簡單來說就是大量的直接定義，例如裡面的RCCType，直接對應RCC register的位址，每個位址會是32 bits 的空間，可以和stm32的文件內容一一對應，
下面是我針對[STM32f1](https://www.datasheetarchive.com/whats_new/eb5b7a65d1b27a7d6441c95509eb5d85.html)修改後的RCC內容：   
```rust
pub struct RCCType {
    pub CR: uint32_t,
    pub CFGR: uint32_t,
    pub CIR: uint32_t,
    pub APB2RSTR: uint32_t,
    pub APB1RSTR: uint32_t,
    pub AHB1ENR: uint32_t,
    pub APB2ENR: uint32_t,
    pub APB1ENR: uint32_t,
    pub BDCR: uint32_t,
    pub CSR: uint32_t,
}
```
在最後面，它用函式宣告傳回對應的Type struct：   
```rust
#[inline(always)]
pub fn RCC() -> &'static mut RCCType {
    unsafe {
        &mut *(RCC\_BASE!() as *mut RCCType)
    }
}
```
而 `RCC_BASE!()` 這個Macro，又會照[上一篇]({{< relref "2015_rust_macro.md">}})提到的 `Macro_rule` 展開為：  
```rust
AHB1PERIPH\_BASE!() + 0x3000u32   
```
一路展開，最後得到一個32 bits integer，再轉型成RCCType 的mutable pointer，我做的修改就是把RCC, USART2, GPIO的位址換成STM32f1的。   
在main 裡面就可以使用 `let rcc = RCC()` 的方式，取得RCC的pointer，並用像C一樣的操作手法來操作對應的register位址。   
例如要修改APB1ENR，啟動週邊的clock:   
```rust
let rcc = RCC();
rcc.APB1ENR |= 0x00020000u32;
```
或是對usart2 的位址取值都沒問題：   
```rust
let usart2 = USART2();
while(true) {
    while(usart2.SR & 0x0080u16 == 0) {}
    usart2.DR = 'x' as uint16\_t;
}
```
這裡我們只輸出'x'，這是因為要把text 印出來，我們需要對str 作iterate，而這個東西是定義在rust 的core lib 裡面，
一般安裝後在 `/usr/lib/rustlib` 裡面只會有 `x86_64_unknown_linux_gnu`，如果要跑arm要先自己編譯arm的lib，
可見[相關的內容](http://spin.atomicobject.com/2015/02/20/rust-language-c-embedded/)：  
這步比較麻煩先跳過，之後研究出來再另文介紹。   

另一個要解決的問題則是 isr\_vector，這裡可以看到一種很謎樣的寫法，用 link\_section 這個attribute，定義區段名為 .isr\_vector，
並設定為一個array，內含一個extern “c” fn()，如果要需要其他的ISR，則可以在後面寫更多的function，並把1改為需要的數量。   
```rust
#[link\_section=".isr\_vector"]
pub static ISRVECTORS: [unsafe extern "C" fn(); 1] = [
    main,
];
```
linker script裡面，先保留一個LONG 的寬度指向初始化stack pointer，接著放isr\_vector的reset handler，再放其他的.text，這樣裝置一上電就會執行main裡的內容。   
```txt
.text :   
{   
    LONG(\_stackStart); /* Initial stack pointer */   
    KEEP(*(.isr\_vector)) /* ISR vector entry point to main */   
    *(.text)   
    *(.text*)   
} > FLASH    
```
如果我們把最終執行檔反組譯，會看到其中的位址配置，0x0指向stack start，0x4 reset\_handler指向位在0x08 的main。：   
```txt
Disassembly of section .text:   
00000000 <\_ZN10ISRVECTORS20h538ad2a8e3805addk6aE-0x4>:   
0: 10010000 .word 0x10010000   

00000004 <\_ZN10ISRVECTORS20h538ad2a8e3805addk6aE>:   
4: 00000009 ....   

00000008 <main>:    
```
執行結果，會印出滿坑滿谷的 'x'，我加一個條件讓它只print 100個：  
![xxx](/images/posts/rust_embedded.jpg)

這份rust code 裡面有用到大量的rust attribute，也就是function 前的#[attribute]，這也可以另外寫一篇文……   
啊感覺挖了自己一堆坑，要趕快填坑了OAO。   

## 結語：

在這篇文我試著解釋如何用rust 撰寫嵌入式系統程式，結論當然是做得到的，但整體比C寫的原始碼複雜得多，也不像C這麼直覺，編輯libarm 也是非常麻煩的工作。   
由於嵌入式系統的code 通常都不會複雜到哪裡去(唔…大概吧)，發揮不出Rust的優勢，我認為比起來還是寫C會有效率得多。