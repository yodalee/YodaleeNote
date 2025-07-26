---
title: "使用 Amethyst Engine 實作小行星遊戲 - 3 連接輸入"
date: 2020-06-29
categories:
- rust
- amethyst
tags:
- rust
- amethyst
series:
- 使用 Amethyst Engine 實作小行星遊戲
forkme: amethyst-asteroid
---

這章有點短，但因為接了鍵盤輸入又要介紹處理輸入的 system 的話，篇幅又太長了，以每章都介紹同樣內容的原則獨立出來；對應為 pong tutorial 的[第三章前半部](https://book.amethyst.rs/stable/pong-tutorial/pong-tutorial-03.html)。  

我們上一章已經寫了幾個 entity 跟 component，這章要開始進到 system，用來操作 entity 跟 component 的內容，在每個 frame system 都會叫起來執行一次，不做事或者做點變動。  
<!--more-->

要接使用者的輸入，我們在 config 下面準備第二個設定檔：config/input.ron。  
```ron
(
    axes: {
        "rotate": Emulated( neg: Key(Left), pos: Key(Right) ),
        "accelerate": Emulated( neg: Key(Down), pos: Key(Up) ),
    },
    actions: {
        "shoot": [[Key(Space)]]
    },
)
```
amethyst 中輸入有兩種形式：axes 和 actions  

* axes 模擬的是兩個不同方向的操作  
如果是搖桿的話應該能讀到類比的輸入，鍵盤則是兩個按鍵的互斥的輸入，兩個按鍵只會判定有一個被按下
* actions 表示數位的輸入，只有按下跟放開兩種狀態  

我們這裡創造兩組 axes 輸入命名為 rotate 跟 accelerate，綁定方向鍵；一個 action 輸入接空白鍵。  

可以綁定的對象當然[不限於鍵盤](https://docs.amethyst.rs/stable/amethyst_input/enum.Axis.html)，比如說 axes 就能綁定鍵盤、控制器（也許是搖桿）、滑鼠、滑鼠滾輪等輸入；
Key 能綁定什麼按鍵則請[參考文件](https://docs.amethyst.rs/stable/amethyst_input/enum.VirtualKeyCode.html)。  

要接輸入，我們要對遊戲的 main.rs 作些修改，加上新的 input\_bundle：  
```rust
use amethyst::input::{InputBundle, StringBindings},

let input_config_path = config_dir.join("input.ron");
let input_bundle = InputBundle::<StringBindings>::new()
       .with_bindings_from_file(input_config_path)?;

let game_data = GameDataBuilder::default()
    // Render, transform bundle here ...
    .with_bundle(input_bundle)?
```
我們產生一個 InputBundle，並用字串來作為讀取 ron 檔案時的 key：也就是上面我們寫的 "rotate", "accelerate" 等。  

這裡我們準備好寫我們第一個 system 了，這裡我們先把所有的 system 都塞在一個 system.rs 裡面，如果分割得更清楚的話，也可以改用 system 的 module 把各系統分到不同的檔案裡面。  
system.rs 的內容如下：  
```rust
use amethyst::{
  core::{Transform},
  derive::{SystemDesc},
  ecs::{Join, ReadStorage, WriteStorage, System, SystemData, Read},
  input::{InputHandler, StringBindings},
};
```

先引入 system 所需要的 module。

```rust
use crate::component::{Ship};

#[derive(SystemDesc)]
pub struct ShipControlSystem;

impl<'s> System<'s> for ShipControlSystem {
  type SystemData = (
    WriteStorage<'s, Transform>,
    ReadStorage<'s, Ship>,
    Read<'s, InputHandler::<StringBindings>>,
  );

  fn run(&mut self,
    (mut transforms,
     ships,
     input): Self::SystemData) {
    for (_ship, _transform) in (&ships, &mut transforms).join() {
      let rotate = input.axis_value("rotate");
      if let Some(rotate) = rotate {
        println!("{}", rotate);
      }
    }
  }
}
```
這個 system 很簡單，去讀 input 的值然後印出來，同樣的 system 也只是一個 struct，我們要實作 `System<'s> trait` ，裡面帶了 run 這個函式，amethyst 引擎會在每個 frame 呼叫各 system 的 run。  
實作 system 時也要指定對應的 SystemData，SystemData 的內容對應 world 裡面儲存的 entity、component 或是 resource。
以我們這個系統為例，它會去修改 transform component、讀取 ship component、讀取使用者輸入。  
在 run 裡，for loop 在下一章會更深入的介紹，這裡我們就是去讀取 input 的 `axis_value`，指定的 key 是 "rotate"，得到對應左右鍵的輸入值，rotate 的值會是 `Some(-1)`, `Some(0)`, `Some(1)` 其中一個。  

最後一步我們要把系統註冊到 game data，在 main.rs 生成 `game_data` 的地方，加上新的 System  
```rust
use crate::system::{ShipControlSystem};

let game_data = GameDataBuilder::default()
    // Render, transform bundle here ...
    .with_bundle(input_bundle)?
    .with(ShipControlSystem, "ship_control_system", &["input_system"]);
```

執行遊戲的時候，試按左右鍵就能看到在終端機上輸出值的變化了。
