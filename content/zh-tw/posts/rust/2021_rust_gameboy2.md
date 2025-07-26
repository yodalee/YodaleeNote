---
title: "Rust Gameboy Emulator Sprite/Joypad"
date: 2021-04-04
categories:
- rust
tags:
- gameboy
- emulator
- rust
series: null
forkme: ruGameboy
---

故事是這樣子的，距離我上一篇 2020/12/20 發的 [rust gameboy emulator]({{< relref "2020_rust_gameboy.md" >}}) 技術文之後，
已經過了兩個月了，中間除了整理積存已久的[天能]({{< relref "/posts/movie/tenet.md" >}})舊文（還有過年），感覺 blog 已經荒廢了QQ。

其實不是的，中間也花了很多時間在 debug 我的 rust gameboy emulator，只是堪稱進度緩慢，主要的原因在於雖然 emulator 可以運作，
卻缺乏 debug 的機制，即使到目前為止，debug 方式仍不脫用肉眼去掃執行的 log，這樣 debug 的效率極度糟糕而且我還不知道要怎麼改進。  
理想上是要弄一個 debug 的介面，可以像 gdb 一樣停在某個記憶體位置，然後印出當下的暫存器內容等等，不過即便我做出來，
當做我參考答案的其他實作也不會有同樣的東西可用，所以後來我放棄實作這個部分。

即便如此，在這兩個月還是完成了不少事情，也在 github 上得到一位 [justapig9020](https://github.com/justapig9020) 大大
（呃…只是一隻豬9020 大大）的幫助，幫我實作了不少東西，像是加上 clap-rs，放大畫面的選項等等。
<!--more-->
最近覺得內容量差不多了，就來寫個簡單的回顧文，用 git log 整理一下兩個月的實作以及一些 LR35902 的內部細節：

## Sprite 記憶體

我們在上一篇[顯示](https://yodalee.me/2020/12/2020_rust_gameboy/#%E9%A1%AF%E7%A4%BA)提到的內容，都是用來顯示背景的記憶體，gameboy 有另一套用來顯示 Sprite 用的記憶體 OAM (Object Attribute Memory)。
上一篇 tetris 啟始畫面的截圖，因為少了 OAM 的關係，其實少了一個選單的指標，真實的啟動畫面是長這樣子：
![tetris_memu_OAM](/images/posts/gb_tetris_OAM.png)
紅框裡的那個小小的三角形就是從 OAM 記憶體畫出來的。

gameboy 總共有 40 個 sprite，記憶體位址從 0xFE00 - 0xFE9F，長度 160 bytes，每個 sprite 4 bytes 的空間，共有以下內容：

|Byte|內容|
|----|-|
| Byte 0 | Sprite 右下角的 Y 值(0-255) |
| Byte 1 | Sprite 右下角的 X 值(0-255) |
| Byte 2 | Tile index，和背景一樣，每個 sprite 的尺寸是一個或兩個 tile，可以用 byte 3 設定 |
| Byte 3 bit 7 | Priority flags |
| Byte 3 bit 6 | True => Flip Y |
| Byte 3 bit 5 | True => Flip X |
| Byte 3 bit 4 | 設定用 OBJ1PAL 或 OBJ2PAL 調色盤 |

因為 X, Y 是右下角，因此如果把 X, Y 設定成 0，就能讓 sprite 看不到。  
和背景時一樣， OAM 記憶體也是記錄 Tile Index，內容固定為 0x8000 - 0x9000 的儲存空間，不像背景可以切換為 0x8800-0x9800。  
Tile 記憶體尺寸是 8x8 (一個 tile) 或 8x16 (兩個 tiles)，透過 hardware IO line 0xFF40 修改 GPU LCD controller register 的 flag；
在 8x16 的模式下，tile index 的 LSB 會被忽略，0, 1 分別指向上下兩塊 tile。  

實作上當然就是把各 field 對應到程式碼：
```rust
#[derive(Default,Clone,Copy,Debug)]
pub struct Sprite {
  tile_idx: u8,
  x: isize,
  y: isize,
  priority: bool,
  flip_y: bool,
  flip_x: bool,
  palette_number: bool
}
```

另外在 bus 的部分把 0xFE00 - 0xFE9F 的位址轉接給 Gpu，store 的時候 Gpu 會去更新內部的 40 個 Sprite。  
顯示的部分也拆成兩階段，第一階段會先畫上背景，第二階段再畫上 sprite，算是流程上的小改動。

簡單講起來是這樣，但 OAM 的實作還有超多細節，包括：
1. 哪個 sprite 的權限比較高？如果重疊的話是 x 值比較小的比較高顯示在前面，x 值相同的話是位址在前的 Sprite 比較高 （0xFE00 最高）
2. GPU 設定裡也有三個不同的調色盤，可以將 00, 01, 10, 11 映射到不同的像素上
    1. 0xFF47 背景調色盤 BGP
    2. 0xFF48 第一個 Sprite 調色盤 OBJ1PAL
    3. 0xFF49 第二個 Sprite 調色盤 OBJ2PAL
3. 透過不同的設定，可以讓 sprite 出現在背景前或背景後，視背景的顏色而定。

目前我的實作應該也還沒考慮完全，特別是第一點顯示權限的地方，絕對還有 bug 要修。

## Joypad 輸入

接完 sprite 之後就是改輸入的部分，不然畫面只會靜止在起始畫面不會動。
Gameboy 的輸入由 hardware IO line 0xFF00 控制，這個 register 的位元分配如下：

| Bit | |
|-|-|
| Bit 6, 7 | Not Used |
| Bit 5 | Output Pin P15 |
| Bit 4 | Output Pin P14 |
| Bit 3 | Input Pin P13 |
| Bit 2 | Input Pin P12 |
| Bit 1 | Input Pin P11 |
| Bit 0 | Input Pin P10 |

由 P15, P14 跟 P13-P10 組成一個 2x4 的陣列：
| | P14 | P15 |
|-|-|-|
| P10 | Right | A |
| P11 | Left | B |
| P12 | Up | Select |
| P13 | Down | Start |

這是什麼意思呢？我看文件裡的範例 code 很久之後才看出來：  
正常狀態 0xFF00 的值是 0x30，要讀取的時候 gameboy 會先對 0xFF00 寫入 0x20 或是 0x10 ，
分別對應我要讀取 P14 跟 P15 的值（low triggered），寫入後再讀取 0xFF00 的值，有按下的鍵，對應的 bit 會讀取到 0，未按下則是 1。

### Joypad 實作
和其他的實作一樣，Joypad 裝置一樣附加在 bus 下面：
```rust
pub struct Joypad {
  p14: u8,
  p15: u8,
  mask: u8,
}
```

若對 0xFF00 寫入的時候，就會存入 mask 當中，讀取的時候則會視 mask 是 0x10 或 0x20 來回傳 p14 或 p15 的值：

```rust
impl Device for Joypad {
  fn load(&self, _addr: u16) -> Result<u8, ()> {
    match self.mask {
      0x20 => Ok(self.p14), // read P14: Left, Right, Up, Down
      0x10 => Ok(self.p15), // read P15: A, B, Select, Start
      _ => Ok(0x0F)     // other value just read nothing
    }
  }

  fn store(&mut self, _addr: u16, value: u8) -> Result<(), ()> {
    self.mask = value;
    Ok(())
  }
}
```

最後是兩個公開的介面 presskey 和 releasekey，以 enum 作為參數讓外界設定
```rust
pub fn presskey(&mut self, key: JoypadKey) {
  match key {
    JoypadKey::RIGHT  => self.p14 &= !0x01,
    JoypadKey::LEFT   => self.p14 &= !0x02,
    JoypadKey::UP     => self.p14 &= !0x04,
    JoypadKey::DOWN   => self.p14 &= !0x08,
    JoypadKey::A      => self.p15 &= !0x01,
    JoypadKey::B      => self.p15 &= !0x02,
    JoypadKey::SELECT => self.p15 &= !0x04,
    JoypadKey::START  => self.p15 &= !0x08,
  }
}
```

minifb 接下的鍵盤事件後，透過這兩個函式設定 p14, p15 的值，如此就完成 joypad 輸入了。  
神奇的是，我這樣改完 tetris 竟然就可以玩了！

{{< video src="/video/tetris.mp4" >}}
## bug fix

上面的影片仔細看的話，會發現分數的地方怎麼怪怪的，
後來發現是 [DAA instruction](https://stackoverflow.com/questions/8119577/z80-daa-instruction) 實作上出了問題，
這個指令真的是怎麼看怎麼怪。  
另外還有一些指令在 flag 上設定的錯誤，也是對執行 log 對了很久才抓出來，感覺真的要有些更有效率的除錯方式才行 (yay)

這次的 Gameboy 開發就到這裡了，近期有點事情開發進度應該會慢些，不過我已經想好下一個目標要做什麼了；
理論上順利的話，也會把這個題目丟去 2021 COSCUP 的 Rust 議程軌（如果有的話），看看今年有沒有機會再次登上 COSCUP。