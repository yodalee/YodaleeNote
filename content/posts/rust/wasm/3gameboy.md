---
title: "使用 Rust 開發 WebAssembly 程式 - 3 Gameboy"
date: 2021-05-22
categories:
- rust
- webassembly
tags:
- rust
- webassembly
- gameboy
- emulator
series:
- 使用 Rust 開發 WebAssembly 程式
---

在我們看過兩個官方文件的範例之後，可以開始寫點真正的 code 了，如之前所言，我們要把 gameboy 移植到 WebAssembly 上面，
這篇文可以說明這到底有多簡單，我覺得已經很接近所謂的 "Code Once, Run Anywhere" 了。
<!--more-->

## 改裝 gameboy

把 gameboy 移到 WebAssembly 的第一步，是先改動 gameboy 的 code，把介面的部分跟實體的內容分開來，
不然我在 wasm-pack build 進行編譯的時候，會有 minifb 用到 [getrandom](https://docs.rs/getrandom/0.2.2/getrandom/#unsupported-targets) 
的亂數功能在 wasm32-unknown-unknown 無法編譯，因為亂數功能的實作需要 system call，
需要 wasm32-wasi 或 wasm32-unknown-emscripten 才編得起來。

以下是我 gameboy Cargo.toml 本來的相依套件，編譯目標是 src/main.rs：
```toml
[dependencies]
log = "0.4.11"
env_logger = "0.8.2"
minifb = "0.19.1"
num-traits = "0.2"
num-derive = "0.3"
clap = "2.33.3"
```

首先我們先把我們的 Gameboy 轉換成一個 library，新增編譯目標：
```toml
[lib]
name = "ru_gameboy"
path = "src/lib.rs"
```

一般來說 Cargo.toml 裡面，可以設定
1.    單一目標如 src/lib.rs src/main.rs
2.    單一函式庫 src/lib.rs 及多個執行檔

第一個可以不用特別設定， cargo 會自己找到編譯對象；第二個的設定則如下：
```toml
[lib]
name = "ru_gameboy"
path = "src/lib.rs"

[[bin]]
name = "ru_gameboy_minifb"
path = "bin/minifb.rs"
```

這樣就能同時編譯 library 和多個 binary，因為我們設定 [[bin]]，如果要編譯出其他的執行檔，只要和這條一樣新增更多 name, path 的組合即可。

但是，這樣子的設定有個問題，因為截至目前為止，Cargo.toml 還沒有辦法為 [lib] 跟 [[bin]] 設定不同的相依套件，
根據 [Github Issue]( https://github.com/rust-lang/cargo/issues/1982) 這是從 2015 開始就被敲碗但也一直被駁回的功能，
所以就算將函式庫跟執行檔分開，我們在編譯 wasm 的時候還是會拉到那些不能編成 wasm 的套件。

參考 [stackoverflow 的回答]( https://stackoverflow.com/questions/35711044/how-can-i-specify-binary-only-dependencies)，
目前只有以下幾種解法：
1.    把 binary 移在 examples 裡面，並設定專給 examples 用的 [dev-dependencies]。
2.    為每個 dependencies 設定 features optional，並在 binary 設定 required-featured，但這樣如果有多個 binary 設定也會愈來愈複雜。
3.    把 binary 分到不同的資料夾內，做成獨立的 project。

我個人選擇也是推薦的會是第三種方法啦，每個目標就是一個獨立的 Cargo.toml，簡單清楚好維護，改造如下：
```txt
ru_gameboy/
    Cargo.toml
    minifb/
        Cargo.toml
        main.rs
    src/
        lib.rs
```

在根目錄的 Cargo.toml 拿掉 clap, minifb 等等圖形顯示需要的相依套件，編譯目標只剩 library。
```toml
[package]
name = "ru_gameboy"
version = "0.1.0"
authors = ["yodalee <email>"]
edition = "2018"

[dependencies]
log = "0.4.11"
num-traits = "0.2"
num-derive = "0.3"

[lib]
name = "ru_gameboy"
path = "src/lib.rs"
```

新檔案 src/lib.rs ，內容就是把這個函式庫所有編譯目標寫進去，並公開唯一一個外部可用的介面 vm.rs：
```rust
pub mod vm;
mod bus;
mod cpu;
mod gpu;
mod instruction;
mod joypad;
mod memory;
mod register;
mod timer;
```

在 minifb 內部的 Cargo.toml 則有全副相依套件，關鍵的 gameboy library，則是用 path 指向上一層 library 所在的位置：
```toml
[package]
name = "ru_gameboy_minifb"
version = "0.1.0"
authors = ["yodalee <email>"]
edition = "2018"

[dependencies]
log = "0.4.11"
env_logger = "0.8.2"
minifb = "0.19.1"
clap = "2.33.3"
ru_gameboy = { version = "0.1", path = "../" }
```

另外還有一些跟介面有關的修改，例如外面需要知道 gameboy 的 JoypadKey，所以把對應的 enum 從 joypad.rs 搬到公開的 vm.rs。

## WebAssembly Gameboy

整頓完 rust gameboy，讓我們實作 WebAssembly，如前兩篇文的介紹，首先利用 cargo-generate 的方式產生好 project，命名為 wasm-gameboy。
```bash
cargo generate --git https://github.com/rustwasm/wasm-pack-template
```

在 Cargo.toml 裡面，加上我們剛剛改好的 ru_gameboy 的相依，這個設定其實和我們 minifb 的設定是一樣的，畢竟 minifb, javascript + WebAssembly 都只是我們 library 的一個顯示介面的實作而已。
```toml
ru_gameboy = { path = "../ru_gameboy" }
```

我們已經看過怎麼不要在 javascript 跟 WebAssembly 之間來回複製記憶體，這樣就直上這個實作，從 ru_gameboy 引入 gameboy vm，
公開給 javascript 的資料結構有兩個：Pixel 跟 Gameboy：

```rust
use wasm_bindgen::prelude::*;
use std::ptr;
use ru_gameboy::vm::{WIDTH, HEIGHT, Vm};

#[wasm_bindgen]
#[repr(u8)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Pixel {
  Black = 0,
  DGrey = 1,
  LGrey = 2,
  White = 3
}
 
#[wasm_bindgen]
pub struct Gameboy {
  pixels: Vec<Pixel>,
  vm: Option<Vm>,
  cartridge: Vec<u8>,
}
```

因為我 Gameboy 設計的關係，vm 一開的時候卡匣的記憶體就要準備好，但是網頁打開生成 WebAssembly 的時候，
使用者一定還沒上傳卡匣，所以這裡的設計是：
* Gameboy.vm 是 Option，初始為 None
* cartridge 的空間 `Vec<u8>` 先開好，等待 javascript 寫入
* 卡匣寫入後就能初始化 vm 為 `Some<Vm>`

實作 Gameboy 的函式，所有函式都向 javascript 公開；constructor 就是分配兩塊記憶體給 Pixels 跟 cartridge 的空間：
```rust
#[wasm_bindgen]
impl Gameboy {
  pub fn new() -> Self {
    let pixels = vec![Pixel::Black;WIDTH * HEIGHT];
    let cartridge = vec![0;0x8000];
    Self {
      pixels,
      vm: None,
      cartridge,
    }
  }
  pub fn width(&self) -> u32 {
    WIDTH as u32
  }
  pub fn height(&self) -> u32 {
    HEIGHT as u32
  }
```

為了讓 javascript 可以取用 WebAssembly 裡面畫面跟卡匣的記憶體，需要兩個 getter 回傳記憶體的指標：
```rust
pub fn get_buffer(&self) -> *const u32 {
  match self.vm {
    Some(ref vm) => vm.buffer.as_ptr(),
    None => ptr::null(),
  }
}
pub fn get_cartridge(&self) -> *const u8 {
  self.cartridge.as_ptr()
}
```

當 javascript 設定好 cartridge，我們就能用 cartridge 的資料來初始化 vm；以及 tick 函式讓 vm 跑起來：
```rust
pub fn set_cartridge(&mut self) {
  self.vm = Some(Vm::new(self.cartridge.clone()));
}

pub fn tick(&mut self) {
  if let Some(ref mut vm) = self.vm {
    vm.run();
  }
}
```

這些函式基本上只是 Rust 函式的封裝而已，編寫起來非常簡單。

## javascript 介面：

### html：
html 如下，提供上傳檔案用的 input；顯示用的 canvas 跟顯示 log 用的 pre：
```html
<input type="file" id="file-uploader"/>
<canvas id="gameboy-canvas"></canvas>
<pre id="gameboy-log"></pre>
```

### javascript：
因為小弟的 javascript 很廢，結果寫 javascript 的時間竟然比寫 rust 的時間還要久…。

開頭我們先定義一些需要的東西：
```javascript
import { Gameboy, Pixel } from "wasm-gameboy";
import { memory } from "wasm-gameboy/wasm_gameboy_bg";

const PIXEL_SIZE = 5;
const COLOR_BLACK = "#000000";
const COLOR_DGREY = "#555555";
const COLOR_LGREY = "#AAAAAA";
const COLOR_WHITE = "#FFFFFF";

const gameboy = Gameboy.new();
const width = gameboy.width();
const height = gameboy.height();

const pre = document.getElementById("gameboy-log");
const canvas = document.getElementById("gameboy-canvas");
canvas.height = PIXEL_SIZE * height;
canvas.width  = PIXEL_SIZE * width;
```

檔案上傳的部分，利用 gameboy.get_cartridge 可以取得卡匣記憶體所在的位置，
用這個位置生成 Uint8Array，就能把上傳的資料寫入 WebAssembly 的卡匣位置，
呼叫 set_cartridge 讓 vm 完成初始化，並設定每 17 ms (60 fps) 呼叫一次 renderLoop 函式。
```javascript
const fileUploader = document.getElementById("file-uploader");

fileUploader.addEventListener('change', (e) => {
  var reader = new FileReader();

  reader.onload = function() {
    const cartridge = gameboy.get_cartridge();
    var bytes = new Uint8Array(reader.result);

    const len = 0x8000;
    const m_cartridge = new Uint8Array(memory.buffer, cartridge, len);
    for (let idx = 0; idx < len; idx++) {
      m_cartridge[idx] = bytes[idx];
    }
    gameboy.set_cartridge();

    setInterval(() => {
      requestAnimationFrame(renderLoop);
    }, 17)
  }

  reader.readAsArrayBuffer(e.target.files[0]);
});
```

renderLoop 很單純，呼叫 tick 讓 gameboy 更新一次畫面，drawPixel 呼叫 get_buffer 拿到顯示所在的記憶體，
在上面產出 Uint32Array 來存取內容，最後在 canvas 上畫出畫面；
在實作上有讓網頁顯示一下 gameboy 的 dump，當初是 debug 用的，這個實作就先跳過。  

```javascript
const renderLoop = () => {
  drawPixels();
  gameboy.tick();
  pre.textContent = gameboy.dump();
}

const drawPixels = () => {
  const buffer = gameboy.get_buffer();
  const pixels = new Uint32Array(memory.buffer, buffer, width * height);
  ctx.beginPath();

  for (let row = 0; row < height; row++) {
    for (let col = 0; col < width; col++) {
      const idx = getIndex(row, col);

      if (pixels[idx] == 0x00000000) {
        ctx.fillStyle = COLOR_BLACK;
      } else if (pixels[idx] == 0x00555555) {
        ctx.fillStyle = COLOR_DGREY;
      } else if (pixels[idx] == 0x00AAAAAA) {
        ctx.fillStyle = COLOR_LGREY;
      } else {
        ctx.fillStyle = COLOR_WHITE;
      }

      ctx.fillRect(col * PIXEL_SIZE, row * PIXEL_SIZE, PIXEL_SIZE, PIXEL_SIZE);
    }
  }

  ctx.stroke();
};
```

這邊是我 gameboy library 的設計問題，因為 minifb 在輸入上用 u32 作為輸入，24 位元代表顏色， 所以我 library 的輸出就是直接寫出 u32，
但以實際狀況來看， 應該是用公開的 repr(u8) enum 作為輸出（反正 gameboy 也只有四個顏色…），
讓外界自己去解釋要顯示什麼就好，這應該是未來可以改進的方向。  
另外我也好奇，能不能從 WebAssembly 直接吐顏色給 javascript？這樣 javascript 不用像這樣把 gameboy 輸出翻譯成顏色，目前我查到感覺是不行，
如果有大大知道的話希望能告訴小弟。

## 跑起來

![wasm gameboy tetris](/images/posts/wasm_rust/wasm_gameboy.png)

就如之前截圖所示，這樣 gameboy 模擬器就會動了，超級簡單，當然我還沒從 javascript 接鍵盤輸入，~~因為我懶得寫 javascript~~。

依照我之前開發 WebAssembly 的經驗，在那邊搞 emscripten 什麼的最後都動不起來，沒有一次像這個這麼簡單，
甚至從這篇也可以看到，只要你 rust 寫完，沒有用到特別的函式庫，介面架一架就可以直上 WebAssembly 了，
我覺得稱 rust 為 WebAssembly 最佳開發工具應該不算太誇張的說法。