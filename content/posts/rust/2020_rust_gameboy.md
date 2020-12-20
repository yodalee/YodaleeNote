---
title: "Rust Gameboy Emulator"
date: 2020-12-20
categories:
- rust
tags:
- gameboy
- emulator
- rust
series: null
---

故事是這樣子的，之前看了網路上有個人寫了一份手把手教你寫一個 risc-v 模擬器 [Writing a RISC-V Emulator in Rust](https://book.rvemu.app)，
雖然後來發現他文件也就一些些，後兩章沒寫不說，中間的手把手也是先伸出手，快握到的時候把手抽回去（欸，總之沒有寫得很詳細，一定要自己去看 code。  

於是小弟就想說來仿造一下，但寫 rvemu 超級費工，決定選一個簡單一點的平台來實作，就選了一款經典處理器 z80 / LR35902，會選這個平台是因為：

1. 簡單好玩，能實作 LR35902，就能玩一些古早的 gameboy 遊戲，效果十足。
2. 最近看到傳說中的 jserv 大大寫了這個 CPU 的模擬器，你各位~~十年 J 粉~~還不快用 rust 寫一個尬廣跟上，~~證明 rust 是世界上最好的程式語言~~。

總之就是寫了，從 11 月中開始到現在大概一個月，費了千辛萬苦，先寫個簡單的整理文，進度到可以顯示出 Tetris 的遊戲選單，如下所示：  
![gb_tetris](/images/posts/gb_tetris.png)
<!--more-->

----

我的 emulator 在架構上跟 rvemu 是類似的，如下圖所示：  

![gb_architecture](/images/posts/gb_architecture.png)

CPU 當頭，往下透過匯流排 Bus 連接不同的裝置，每個裝置都會有對應的記憶體位址。  

以下就分別介紹各個部分：

## CPU

CPU 做的事情很簡單，就是持續不斷進行取出指令並執行，gameboy 的 LR35902 只有八個八位元的暫存器，兩兩一組命名為 AF、BC、DE、HL。

* A 表示 Accumulator，運算指令都是指定目標，然後做 A = A ⊕ Target
* F 表示 Flag，LR35902 共有四個 flag，Zero、Subtract、Half Carry 跟 Carry，
我的實作是自己實作專用的 `struct FlagRegister` 記錄四個 boolean 值，存取的時候實作跟 u8 之間的互相轉換；
也有其他人的實作是直接存 u8，然後用介面封裝存取 flag 的位元運算。
* BC, DE 就是一般的暫存器
* HL 比較特殊，有指令可以直接存取 HL 組合成 16 bits 的位址。

另外 CPU 必要的兩個東西當然就是 stack pointer (SP) 跟 program counter (PC)，用 u16 表示。

## Instruction

Instruction 應該是個人最自豪的部分了（自己說）。  
[LR35902](https://www.pastraiser.com/cpu/gameboy/gameboy_opcodes.html)
 （底層的處理器源自 [Z80](https://clrhome.org/table/)，但又有一些任天堂自己修改的地方）共 245 個指令，如果一對一去寫就要寫 245 種變化。

而我們借助 rust 的 enum，可以輕易將 LR35902 的指令集分門別類，例如中間 0x4x-0xBx 的指令集，
都只是同樣指令作用在不同的暫存器上面，因此我們可以這樣寫：

```rust
type Source = Target;
enum Target {
  A, B, C, D, E, H, L, HL //...
}

type Source = Target;
enum Instruction {
  LDRR(Source, Target),
  ADD(Target),
  ADC(Target),
  SUB(Target),
  SBC(Target),
  AND(Target),
  XOR(Target),
  OR(Target),
  CMP(Target),
}
```
九個 enum 就能表示 128 個指令，在 CPU 的實作上也清爽很多，400 行就足以搞定 245 指令的實作，
~~不用一個檔案寫到 3000 行~~，當然效能好不好就…嗯…不好說。

另外像是 0xcb prefix instruction，也只是對不同的暫存器進行不同的位元操作，同樣用 enum 只要這樣就可以表示完了：
```rust
enum CBInstruction {
  RLC(Target),
  RRC(Target),
  RL(Target),
  RR(Target),
  SLA(Target),
  SRA(Target),
  SWAP(Target),
  SRL(Target),
  BIT(Target, u32),
  RES(Target, u32),
  SET(Target, u32),
}
```

有關每個指令的詳細內容，可以參考下面這個 [Gameboy CPU manual](http://marc.rawer.de/Gameboy/Docs/GBCPUman.pdf)，
不過我大部分還是直接去看其他 project 的實作，像是另一個用 rust 實作的 [sgb](https://github.com/jeremycochoy/sgb)，
不然 manual 實在寫得有點不明不白。

## Bus

Bus 附屬在 CPU 之下，負責管理 CPU 可以存取到的記憶體，LR35902 的記憶體用 16 bits 定址，共 64 K，參見 [memory map](http://gameboy.mongenel.com/dmg/asmmemmap.html)。  
要跑出 Tetris 的畫面，會需要實作的區塊包括：

* 0x0000 - 0x7999：卡匣（這部分應該是唯讀）
* 0x8000 - 0x9FFF：VRAM（由下文 GPU 負責處理）
* 0xC000 - 0xDFFF：RAM
* 0xFE00 - 0xFE9F：目前是用 Memory 但未來有可能搬給 GPU 處理
* 0xFEA0 - 0xFEFF：Unusable Memory，不知道為什麼 unusable 卡匣裡的程式偏偏要用？我本來只要存取這塊就會回 Err 的
* 0xFF00 - 0xFF79：硬體 IO 線，這可能是 bus 裡面最複雜的部分，目前的實作也是我最不滿意的。
* 0xFF80 - 0xFFFE：High RAM
* 0xFFFF：Interrupt Enable

記憶體就是把一個 `Vec<u8>` 包起來當作記憶體，每宣告一塊記憶體都要連帶宣告它的起始位址(base)，並實作 Device trait 裡的 load/store 兩個函式。
```rust
pub struct Memory {
  base: usize,
  memory: Vec<u8>,
}

pub trait Device {
  fn load(&self, addr: u16) -> Result<u8, ()>;
  fn store(&mut self, addr: u16, value: u8) -> Result<(), ()>;
}
```
bus 會 match load/store 的 addr 並選擇正確的記憶體區塊呼叫對應的 load/store，
實作 Device 的裝置再自行計算扣掉起始位址的位址，存取對應的 `Vec<u8>`。
下面要提到內部包了 VRAM 的 GPU；或是 Timer 接了三條硬體 IO 線，也是一樣實作 Device trait，讓 bus 把存取的呼叫直接 dispatch 給他們。  

bus 的 load 實作大概像是這樣：
```rust
fn load(&self, addr: u16) -> Result<u8, ()> {
  match addr {
  CATRIDGE_START ..= CATRIDGE_END => self.catridge.load(addr),
  VRAM_START ..= VRAM_END => self.gpu.load(addr),
  RAM_START ..= RAM_END => self.ram.load(addr),
  OAM_START ..= OAM_END => self.oam.load(addr),
  UNUSABLE_START ..= UNUSABLE_END => {
    info!("Load at unusable address {:#x}", addr);
    Ok(0)
  }
  HRAM_START ..= HRAM_END => self.hram.load(addr),
  TIMER_START ..= TIMER_END => self.timer.load(addr),
}
```

## GPU

以下先整理一下 LR35902 的 GPU 架構：  
硬體參考資料：[Game boy Architecture](https://www.copetti.org/projects/consoles/game-boy)  
時序參考資料：[Gameboy Emulator in Javascript : GPU Timing](http://imrannazar.com/GameBoy-Emulation-in-JavaScript:-GPU-Timings)  

Gameboy 實體的顯示空間為 160 x 144 pixel，CRT 顯示器會由左至右、由上而下、~~反覆觀察~~更新每個 pixel。  
在實際硬體上，每次更新畫面會從兩個不同的地方取得資料， VRAM (Tile) 和 OAM (Sprite)，目前只實作了 VRAM；
硬體每掃描完一條線，就會進入 HBlank，把掃描點移動到下一行行首；掃到最後一行會進入 VBlank，把掃描點移動回螢幕開頭。
![gb_display](/images/posts/gb_display.png)

軟體上我們把 VRAM 跟 OAM 分開成不同的模式，因此 GPU 會處在四個不同的模式，每個模式持續時間如下：

| Mode | Cycle |
|:-|:-|
| Scanline OAM | 80 |
| Scanline VRAM | 172 | 
| HBlank | 204 |
| VBlank | 4560 (456 cycles * 10 lines) |
| Total | 70224 |

以 Gameboy clock 的速度 4MHz 來看，應該可以跑到 60 Hz 的更新頻率，是不是有點快R…。

在 Gameboy 的那個時代，CPU 和顯示卡的同步是個大問題，依照我看的資料顯示，CPU 只能在螢幕處在 VBlank 的時候，才能去存取顯示記憶體。  
硬體 Youtuber [Ben Eater](https://eater.net) 最近在[幫 6502 電腦安裝~~世界上最爛~~的顯示卡](https://www.youtube.com/watch?v=2iURr3NBprc)，
在 4:00 左右也有提到類似的東西，古早味的記憶體不像現在的雙倍資料率（DDR）記憶體，
能夠在一個時脈內進行多次的讀寫，所以 GPU 和 CPU 必須在不同時間內存取記憶體。  

在 LR35902 上，這個工作由位址 0xff44 的硬體 IO 線達成，可以從這個位址得到現在 GPU 掃描的行數，
Tetris 的程式裡，也有迴圈不斷檢查 0xff44，行數在 VBlank 的時候才會離開迴圈；
同時在 GPU 進到 VBlank mode 的時候，也會發送一個 interrupt 給 CPU，讓 CPU 可以做對應的處置。

## 顯示

Gameboy 的虛擬顯示空間為 256 x 256 pixels，內部實作為稱為 tile 的單位。
每個 tile 大小 8 x 8 pixels，虛擬空間為 32 x 32 tiles，每個 tile 大小為 16 bytes，一個像素由兩個 bit 表示四個色階：黑、深灰、淺灰、白。

Gameboy 的 VRAM 大小 8KB，功能細分如下：  

### 0x8000 - 0x97FF：
這塊 6144 bytes 的空間，可以從 hardware IO line 設定要使用前面的 0x8000 - 0x9000 或後半的 0x8800 - 0x9800。
儲存 tile 的資訊，4K 可以儲存 4K / 16 = 256 tiles。
注意到實體顯示畫面的尺寸是 20 x 18 = 360 tiles，這比可儲存的 256 tiles 還多，也就是說，在 gameboy 上執行的遊戲，畫面上一定有複數格顯示一樣的東西。

### 0x9800 - 0x9BFF：
這塊 1024 bytes 的空間，每個 byte 指定虛擬顯示空間 32 x 32 tiles ，每個 tiles 要對應到哪個 tile，一個 bytes 能表示 0 到 256，正好對應儲存的 tile 數量。

tile 內容的儲存方式有點複雜，簡單畫個圖大概是這樣（這張圖好像滿考驗看倌螢幕的顯色能力）：
![gb_tile](/images/posts/gb_tile.png)  
每個 tile 的一行（8 個像素）是由兩個 byte 組合而成：  
line[7] = byte1[7] + byte2[7]  
line[6] = byte1[6] + byte2[6]  
依此類推。

我的 gameboy 目前使用 [minifb](https://github.com/emoon/rust_minifb) 來顯示畫面，每當 GPU 進到 VBlank mode 的時候，就會叫 GPU 填一下顯示的 buffer。
概念性的 code 如下：
```rust
pub const WIDTH: usize = 160;
pub const HEIGHT: usize = 144;

let buffer: vec![0; WIDTH * HEIGHT],
while self.cpu.bus.gpu.mode != GpuMode::VBlank {
  self.cpu.step()?;
}
self.cpu.bus.gpu.build_screen(&mut buffer);
window.update_with_buffer(&vm.buffer, WIDTH, HEIGHT).unwrap();
```

## Interrupt：

把上面的東西都做完的話，可以看到 Tetris 開頭的顯示版權的文字畫面，不過會進不了遊戲主選單，因為 Tetris 程式會透過 interrupt 來驅動程式的進行，
來一次 interrupt 檢查一下要不要切換畫面。  
Gameboy 共有五個不同的 interrupt，Interrupt 進來的時候，CPU 將現在的 PC 儲存到 stack，並跳轉到對應的 handler address：

| Type | Priority | Handler address |
|:-|:-|:-|
| VBlank | 1 | 0x40 |
| LCDC | 2 | 0x48 |
| Timer | 3 | 0x50 |
| Serial Transfer | 4 | 0x58 |
| Joypad Input | 5 | 0x60 |

我們這裡只先實作 VBlank interrupt，實作方式很簡單，在 GPU 的模式切到 VBlank 的時候，GPU 內部自行設定 interrupt 的 flag；
CPU 每執行完一個指令，就會檢查以下幾個條件：

1. CPU 內部的 Interrupt 狀態，可以透過 EI/DI 兩個指令控制。
2. 0xFFFF 位址，記錄各 interrupt 是否 enable。
3. GPU flag 有沒有設定，如果是其他的 interrupt 就會去檢查對應裝置內的 flag。

條件都符合，CPU 就立即執行一個 RST 指令，讓 PC 跳轉到 interrupt 對應的 handler。

## 結語

以上就是我們實作 Gameboy - LR35902 的一個 Emulator，可以看到我們實作 CPU ，並模仿一個設備的內部設計，實作匯流排連接各個裝置。  
我們的時序不會是真的，因為在模擬的時候，我們一定是讀取一個指令、執行，然後處理繪圖跟中斷，
但在真實的處理器中並不是這樣，中斷可能發生在任何時候，從中打斷指令的執行，但要模擬到如此精細，顯然要費上十倍以上的功夫。  
目前這個 emulator 也離完成品相差不少，hardware IO 可以對顯示做的設定還沒弄、還沒接使用者輸入、音效卡等等，要做的事還很多。

原始碼公布在 [github](https://github.com/yodalee/ruGameboy) 上面，歡迎大家指教。

----

最近我有一種體會，一般來說資訊工程的課程，無論是作業系統、系統程式、組合語言這幾個圍繞在 CPU 周邊的課程，對於中斷的著墨都是不夠的。  
雖然沒什麼道理，但不知道為什麼大家都喜歡用人體來比喻，所以我也用人體來比喻一下我的觀點：
* CPU 最核心的心臟是時脈，有了心臟才能推動一切指令的運行。
* 匯流排是血管，在時脈的推動下運送資料。
* ALU 是細胞，處理匯流排送來的資料，得出結果交還給匯流排。
* 記憶體是肺臟，輸出入匯流排上的資料。
* 而中斷，則是 CPU 的神經，總管一切對外的連結，沒有中斷的 CPU 就和植物人無異。

CPU 許多行為都有中斷介入，只看程式碼很難明白為什麼控制權會突然從 A 跳給 B，那是在程式之外的硬體邏輯，
舉凡作業系統核心的 scheduling、記憶體、IPC 無不與中斷息息相關。  

> 要能看懂作業系統，學會底層的 C/assembly 是必要的，但要邁向作業系統大師，則必須先掌握中斷。
