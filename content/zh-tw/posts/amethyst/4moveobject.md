---
title: "使用 Amethyst Engine 實作小行星遊戲 - 4 移動物體"
date: 2020-06-30
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

上一章連接輸入的部分，我們完成了第一個 system 的設計，當然這個系統什麼事都沒做，這章我們就來把輸入接到真正的變化上。  
<!--more-->

一開始讓我們在 component.rs 裡面新增一個 component physical：  
```rust
use amethyst::{
  core::math::Vector2,
};

pub struct Physical {
  // velocity, [vx, vy]
  pub velocity: Vector2<f32>,
  // maximum velocity (units / s)
  pub max_velocity: f32,
  // rotation (rad / s)
  pub rotation: f32,
}

impl Component for Physical {
  type Storage = DenseVecStorage<Self>;
}
```

直覺上來想，可能會覺得我們之前產生的 Ship component 裡面應該要有 velocity 屬性，system 會讀取 velocity 去更新太空船的位置 - 也就是 transform。  

但是不對，因為畫面上會動的東西不止有 Ship，之後會新增的子彈跟小行星都是會動的，而實作<會動>都是共通的。  
寫在 Ship 內的性質無法共用，所以我們直接新增一個 physical component 記錄速度和旋轉量，想要動的東西只要加上 physical component 就行了，程式碼共用的部分可以很漂亮的抽出來。  

這裡我們直接使用 nalgebra 的 vector2 來代表速度，amethyst 裡面有包一包 nalgebra 並且重命名為 `core::math`，版本是 0.19.0，這個在我們後面引入 ncollide2d 的時候會帶來麻煩，不過這裡就先用吧。  

state.rs 裡面，在 initialize\_ship 函式幫產生的 entity 加上 Physical component：  

```rust
use crate::components::{Ship, Physical};

world
  .create_entity()
  .with(transform)
  .with(sprite_render.clone())
  .with(Ship::new())
  .with(Physical {
    velocity: zero(),
    max_velocity: 10.0,
    rotation: 0.0
  })
  .build();
```

現在來修改 system，先新增一個操作 Physical component 的 system：  

```rust
#[derive(SystemDesc)]
pub struct PhysicalSystem;

impl<'s> System<'s> for PhysicalSystem {
  type SystemData = (
    ReadStorage<'s, Physical>,
    WriteStorage<'s, Transform>,
    Read<'s, Time>,
  );

  fn run(&mut self,
    (physicals,
     mut transforms,
     time): Self::SystemData) {
    let delta = time.delta_seconds();
    for (physical, transform) in (&physicals, &mut transforms).join() {
      let movement = physical.velocity * delta;
      let rotation = physical.rotation * delta;
      transform.prepend_translation(Vector3::new(movement.x, movement.y, 0.0));
      transform.rotate_2d(rotation);
    }
  }
}
```

每個系統都要定義 SystemData，也就是它需要存取哪些資源，無非就是：

* 讀寫 component
* 新增/刪除 entity
* 讀取 world 內存的 resource

PhysicalSystem 會需要去讀 Physical component、系統提供的 Time resource、寫入 transform component。  
在讀取和寫入有不同的方式，可以參考[文件 system 章節](https://book.amethyst.rs/stable/concepts/system.html)，大致整理起來是：  

*  Read<'s, Resource>、Write<'s, Resource>：取得唯讀/可讀寫的 Resource  
這個是保證不會失敗的取得資源，如果失敗的話會直接給你一個 Default::default() 的版本。
*  ReadExpect<'s, Resource>、WriteExpect<'s, Resource>  
同上，但這個適用在沒有實作 Default::default() 的資源上。
*  ReadStorage<'s, Component>、WriteStorage<'s, Component>  
取得唯讀/可讀寫的 Component 參考。
*  Entities<'s>：創造或刪除 entity 用。

實作 system 只要實作一個 run 函式，這裡有兩種寫法，一種如上面所示，在參數階段就把 SystemData 解開來；另一種則是在函數內解開：  
```rust
fn run(&mut self, data: Self::SystemData) {
  let (physicals,
        mut transforms,
        time) = data;
  // ...
}
```

兩種對編譯器來說應該是一樣的，所以選一個喜歡的就可以了，但記得一個原則，一定要把每一行都分開寫，不要擠在一行：  
```rust
let (physicals, mut transforms, time) = data;
```
這是因為我們的 system 是會長大的，哪天要加一個新的 component，直接加一行會比在一行裡面找到正確的位置還要簡單。  

從 SystemData 拿到的，會是這個遊戲裡「所有有這個 component 的資料」，這裡會收集到所有有 Physical component 的 entity；所以我們用 for loop ，搭配 join() 把資料展開來。  
只要是 component 展開這步幾乎是必要的，我個人是建議從 system data 裡解出來的資料，一律加 s 用複數，用 for 解出來再變單數，變數名詞選同一個，比較不會去考慮哪個是哪個。  
再來就是位移跟旋轉的實作，從 [Time](https://docs.amethyst.rs/stable/amethyst_core/timing/struct.Time.html)
這個 resource 裡面，我們可以拿到和上一個 frame 之間的時間差，配合 physical 裡面記錄的速度和角速度算出位移量，並更新到 transform 就行了。  

上一篇的 ShipControlSystem 也要修改，它會從 ship 定義的加速度算出速度的變化值，修改到 physical 速度內。  
這裡揭示了 for loop 配 join 的用法，從 `ReadStorage<'s, Physical>` 拿到的，是所有「有 physical component」，只想要改 ship，只要把 physicals、ships 一起放進 join 裡面，就會只拿出同時有 physical 和 ship component 的 entity 了：  
```rust
let delta = time.delta_seconds();
for (physical, ship, transform) in (&mut physicals, &ships, &transforms).join() {
  let acceleration = input.axis_value("accelerate");
  let rotate = input.axis_value("rotate");

  // handle acceleration -> velocity
  let acc = acceleration.unwrap_or_default();
  let added = Vector3::y() * delta * acc * ship.acceleration;
  let added = transform.rotation() * added;
  physical.velocity += Vector2::new(added.x, added.y);

  let magnitude = physical.velocity.magnitude();
  if magnitude > physical.max_velocity {
    physical.velocity *= physical.max_velocity / magnitude;
  }
```

最後一步，和上一篇一樣把我們的 system 註冊到 `game_data` 裡面：   

```rust
use crate::system::{ShipControlSystem, PhysicalSystem};

let game_data = GameDataBuilder::default()
  // Render, transform bundle here ...
  .with(ShipControlSystem, "ship_control_system", &["input_system"])
  .with(PhysicalSystem, "physical_system", &["ship_control_system"]);
```

註冊 system 的 [with](https://docs.amethyst.rs/stable/amethyst/prelude/struct.GameDataBuilder.html#method.with) 是可以寫明相依關係的，
三個參數分別是 system struct，system name 和 dependencies list，我們這裡的寫法 `input_system`（這個名字應是預設的）、ShipControlSystem、PhysicalSystem 會依序執行。  
