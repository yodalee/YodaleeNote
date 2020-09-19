---
title: "使用 Amethyst Engine 實作小行星遊戲 - 1 設定專案"
date: 2020-06-26
categories:
- rust
- amethyst
tags:
- rust
- amethyst
series:
- 使用 Amethyst Engine 實作小行星遊戲
---

首先我們要先設定專案，內容會對應官方教學的 [Getting Started](https://book.amethyst.rs/stable/getting-started.html) 和 Pong 的[第一章](https://book.amethyst.rs/stable/pong-tutorial/pong-tutorial-01.html)：  
<!--more-->

設定專案上有幾個方式：

1. amethyst 自己的工具  
個人建議，可以用 Cargo 安裝，比較簡單
2. clone 官方提供的啟動專案，不能帶著走了  
3. 用 Cargo new 生一個空專案  
在 Cargo.toml 裡面加上 amethyst 的 dependency，這個真的很麻煩完全不建議
```shell
cargo install amethyst_tools
amethyst new <game-name>
```

專案會自動新增 Cargo.toml，比較重要的是下面的 features，amethyst 可以選擇依賴的底層 API，
如果是 Linux/Windows 選 Vulkan；蘋果用戶選 Metal；empty 我編譯完成圖形介面會出不來所以就不要用了。  

```toml
[package]
name = "rocket"
version = "0.1.0"
authors = []
edition = "2018"
[dependencies]
amethyst = "0.15.0"
[features]
default = ["vulkan"]
empty = ["amethyst/empty"]
metal = ["amethyst/metal"]
vulkan = ["amethyst/vulkan"]
```

專案建好可以直接先開始編譯，amethyst 框架滿大的，第一次編譯會花上幾分鐘的時間把整個框架給架起來，不過放心，編好一次之後編譯都只要編譯你寫的 code，速度會快很多（雖然說我覺得還是很慢，大概 30 秒至一分鐘不等，Rust 真的很適合[這張圖](https://xkcd.com/303/)）。  
[![](https://imgs.xkcd.com/comics/compiling.png)](https://imgs.xkcd.com/comics/compiling.png)  

預設版本執行起來應該會看到完全空白的畫面，生成的 main.rs 如下所示：  
```rust
use amethyst::{
    core::transform::TransformBundle,
    prelude::*,
    renderer::{
        plugins::{RenderFlat2D, RenderToWindow},
        types::DefaultBackend,
        RenderingBundle,
    },
    utils::application_root_dir,
};
```

一開始當然是引入需要的模組。  
```rust
struct MyState;
impl SimpleState for MyState {
  fn on_start(&mut self, _data: StateData<'_, GameData<'_, '_>>) {}
}
```
定義遊戲的 struct，amethyst 把遊戲分為不同的狀態，例如遊戲開始的時候會載入資源，這時候要顯示載入中；載入完要顯示選單，在 amethyst 裡面這些都是不同的狀態，遊戲本質上來說就是在這些狀態間切來切去。  
Amethyst 使用一個 stack 來管理 state，最上層就是目前執行的 state。  

不過呢，因為現在要做的範例還沒有這麼複雜，state 的部分我們就先跳過，我自己也還沒學會（欸，這應該要等到最後我們開始把遊戲外面包上介面的時候再來學就好了。  

這邊使用 amethyst 提供的 SimpleState trait，它已經幫我們實作了事件的介面，比自己實作完整 state 簡單。  
```rust
fn main() -> amethyst::Result<()> {
  amethyst::start_logger(Default::default());
  let app_root = application_root_dir()?;
  let assets_dir = app_root.join("assets");
  let config_dir = app_root.join("config");
  let display_config_path = config_dir.join("display.ron");
```
進到主程式第一件事就是先打開 logger（然後我找不到怎麼記下 log 的文件…），用來記錄事件/警告/錯誤等等。  

設定 `assets_dir` 跟 `config_dir` 並讀入 display.ron 設定檔，[ron](https://github.com/ron-rs/ron) 是款 rust 專門的格式， config/display.ron 會記錄視窗的標題，還有它的畫面尺寸等資訊：  
```ron
(
  title: "rocket",
  dimensions: Some((1000, 1000)),
)
```
 所有可以設定的選項可以參考 DisplayConfig 的[文件](https://docs-src.amethyst.rs/stable/amethyst_window/struct.DisplayConfig.html)  
 ```rust
   let game_data = GameDataBuilder::default()
    .with_bundle(
      RenderingBundle::<DefaultBackend>::new()
        .with_plugin(
          RenderToWindow::from_config_path(display_config_path)?
        .with_clear([0.34, 0.36, 0.52, 1.0]),
      )
    .with_plugin(RenderFlat2D::default()),
    )?
    .with_bundle(TransformBundle::new())?;

  let mut game = Application::new(assets_dir, MyState, game_data)?;
  game.run();
  Ok(())
}
```

剩下的 main 內容就是把 `game_data` 建起來，預設我們引入兩個 bundle，用來顯示的 RenderingBundle 跟做圖形轉換用的 TransformBundle。
首先我們生一個 RenderingBundle，裡面有兩個 plugin，RenderToWindow 讀入我們寫好的 display.ron 並顯示主視窗；RenderFlat2D 可以在畫面上顯示 Sprite。
最後拿著我們生成的遊戲狀態 `MyState`、 `game_data` 全部塞進 Application 裡面就可以了；看到這麼一大團程式碼，就可以理解為什麼一定要用 amethyst 工具幫我們生出預設的設定了，自己手爆這堆東西一定會累死。

到這邊我們就寫好一個空白視窗的小程式了，下一步我們要在畫面上畫上一些東西。
