---
title: "使用 Amethyst Engine 實作小行星遊戲 - 2 讀入資源"
date: 2020-06-27
categories:
- rust
- amethyst
tags:
- rust
- amethyst
series:
- 使用 Amethyst Engine 實作小行星遊戲
---

畫東西應該是遊戲最基本的功能，除非你是要做什麼矮人要塞之類的 ASCII 遊戲…這種遊戲大概不太有人想玩了。  
Amethyst 使用了一套叫 [specs](https://specs.amethyst.rs/docs/tutorials/) 的 ECS Entity-Component-System 框架，當然，也是 Rust 寫的。  
ECS 概念是：所有的遊戲裡面的物件都是一個 entity（實體），上面可以附上很多的 component（部件，或零件），System（系統）則會去操作這些 component，entity 本身只是帶著 component 走的容器，我們後面實作系統就會更明白這點。  
<!--more-->

我們先來個簡單的重構，創一個新的檔案：`states.rs` 並把在 `main.rs` 裡面的 state 搬出來：  

```rust
use amethyst::{
  assets::{AssetStorage, Loader, Handle},
  core::transform::{Transform},
  prelude::*,
  renderer::{Camera, ImageFormat, SpriteSheet, Texture, SpriteSheetFormat, SpriteRender},
};

pub const ARENA_HEIGHT: f32 = 300.0;
pub const ARENA_WIDTH: f32 = 300.0;

pub struct AsteroidGame;

impl SimpleState for AsteroidGame {
  fn on_start(&mut self, data: StateData<'_, GameData<'_, '_>>) {
    let world = data.world;
  }
}
```

這次我們引入更多的 module：
* 載入資源的 assets
* 控制位置轉換的 transform、Camera
* 顯示 Sprite 用的元件

下面定義我們場地的大小，最後是我們已經熟悉的 State Struct。  
從 StateData 裡面可以拿到遊戲的 world，world 裡面會存有所有遊戲的資料：resource、entity 和 component。  

## Entity

先來產生第一個 entity：一台相機。  
```rust
fn initialize_camera(world: &mut World) {
  let mut transform = Transform::default();
  transform.set_translation_xyz(ARENA_WIDTH * 0.5, ARENA_HEIGHT * 0.5, 1.0);

  world
  .create_entity()
  .with(transform)
  .with(Camera::standard_2d(ARENA_WIDTH, ARENA_HEIGHT))
  .build();
}
```
我們產生一個位移定在遊戲場景中間，Z 為 1.0 的相機，之後產生的物件 Z 軸會定在 0.0 上面。  
Amethyst 的座標是第一象限往右往上愈大，以這個相機的可視範圍來說，左下是 (0.0, 0.0) 右上是 (WIDTH, HEIGHT)；
產生 entity 只需要呼叫 `world.create_entity()` ，並把需要的 component 用 with 塞進去就可以了。  

## Component

來寫第一個 component，開一個新的檔案 components.rs 並填入下面的內容：  
```rust
use amethyst::{
  ecs::prelude::{Component, DenseVecStorage},
};

pub struct Ship {
  pub acceleration: f32,
  pub rotate: f32,
  pub reload_timer: f32,
  pub time_to_reload: f32,
}

impl Ship {
  pub fn new() -> Self {
    Self {
      acceleration: 80f32,
      rotate: 180f32,
      reload_timer: 0.0f32,
      time_to_reload: 0.5f32,
    }
  }
}

impl Component for Ship {
  type Storage = DenseVecStorage<Self>;
}
```

component 沒有什麼特別的，就是單純的一個 struct，在我們實作了 Component 之後，就可以把這個 struct 塞進 entity 裡面，
Component 裡面可以什麼都沒有，單純做個標記；也可以像現在這樣，存有一個 Ship 所需要的性質。  

實作 Component 的時候，都會需要指定不同的儲存方式，specs 裡面有[五種不同的儲存方式](https://specs.amethyst.rs/docs/tutorials/05_storages.html#densevecstorage)可選，
針對存取速度、記憶體用量有不同的最佳化，我們還是小遊戲的時候，基本上無腦的用 DenseVecStorage 就行了。  

## 載入 Sprite。  
回到我們的 states.rs，加上載入 `sprite_sheet` 用的函式庫：  
```rust
fn load_sprite_sheet(world: &World) -> Handle<SpriteSheet> {
  let texture_handle = {
    let loader = world.read_resource::<Loader>();
    let texture_storage = world.read_resource::<AssetStorage<Texture>>();
    loader.load(
      "texture/ship.png",
      ImageFormat::default(),
      (),
      &texture_storage,
    )
  };

  let loader = world.read_resource::<Loader>();
  let sprite_sheet_store = world.read_resource::<AssetStorage<SpriteSheet>>();
  loader.load(
    "texture/ship.ron", // Here we load the associated ron file
    SpriteSheetFormat(texture_handle),
    (),
    &sprite_sheet_store,
  )
}
```
我們把所有圖形資源都放在 assets/texture 裡面，一套資源是一個 png 檔配上一個 ron 檔，ron 檔描述一系列資源的起始座標跟大小，除了 png 檔 amethyst 也能讀入其他的檔案如 3D 模型等；以這邊的 ship.ron 為例，指定圖片大小為 16x16，內含一個 sprite 從 (0,0) 到 (16,16)：  
```ron
List((
  texture_width: 16,
  texture_height: 16,
  sprites: [
    (
    x: 0,
    y: 0,
    width: 16,
    height: 16,
    ),
  ],
))
```
先用 amethyst 內提供的 loader 把整個 png 檔讀進來，變成 world 內部的 texture resource（資源），resource 和 component 類似但不會綁定在某個 entity 上面。  
load 函式會回傳一個 `Handle<Texture>` 指向 `AssetStorage<Texture>` 裡 png 檔被讀進的位置，Handle 的實作類似 reference count pointer，讓所有人都可以共用一個 asset。  
png 檔被讀入 AssetStorage 後，再次使用 loader 把 texture 讀入變成 SpriteSheet，這次回傳的內容會是 `Handle<SpriteSheet>` 指向 `AssetStorage<SpriteSheet>` 中的位置。  

## 整合
最後一步，我們把上面一切都整合起來：  
```rust
fn initialize_ship(world: &mut World, sprite_handle: Handle<SpriteSheet>) {
  let mut transform = Transform::default();
  transform.set_translation_xyz(ARENA_WIDTH * 0.5, ARENA_HEIGHT * 0.5, 0.0);

  let sprite_render = SpriteRender {
    sprite_sheet: sprite_handle,
    sprite_number: 0
  };

  world
    .create_entity()
    .with(transform)
    .with(sprite_render.clone())
    .with(Ship::new())
    .build();
}
```
`initialize_ship` 跟 `initialize_camera` 沒有差太多，參數的 `sprite_handle` 來自剛剛的函式 `load_sprite_sheet`；
位移設定太空船的位置在畫面正中間，從 `sprite_sheet` 產生 `sprite_render`，SpriteRender 就是真的顯示在畫面上的物件了。  
如果一組 sprite 裡面有數個 sprite，可以用 `sprite_number` 去指定要顯示哪個；最後生成 entity 並把 transform、sprite、Ship 三個 component 加上去即可。

有關 Sprite 的部分，因為有點複雜，我簡單整理起來是這個樣子：  

1. 呼叫 Loader 將圖片載入為 Texture -> `Handle<Texture>`
2. 呼叫 Loader 讀 ron 檔，將圖片分割為 SpriteSheet -> `Handle<SpriteSheet>`
3. 從 `Handle<SpriteSheet>` 生成 SpriteRender -> 作為 Component 放到 entity 中

```rust
impl SimpleState for Asteroid {
  fn on_start(&mut self, data: StateData<'_, GameData<'_, '_>>) {
    let world = data.world;

    let sprite_sheet = load_sprite_sheet(world);

    world.register::<Ship>();

    initialize_camera(world);
    initialize_ship(world, sprite_sheet);
  }
}
```
在 state `on_start` 時，呼叫 `load_sprite_sheet` 得到 `Handle<SpriteSheet>`，呼叫 `initialize_camera` 和 `initialize_ship` 初始化 camera 跟 ship entity。  
有一行特別是這行
```rust
world.register::<Ship>()  
```
如果不加這行的話，會遇到執行期錯誤：  

```txt
thread 'main' panicked at 'Tried to fetch resource of type `MaskedStorage<Ship>`[^1] from the `World`, but the resource does not exist.  

You may ensure the resource exists through one of the following methods:  

* Inserting it when the world is created: `world.insert(..)`.  
* If the resource implements `Default`, include it in a system's `SystemData`, and ensure the system is registered in the dispatcher.  
* If the resource does not implement `Default`, insert it in the world during `System::setup`.  

[^1]: Full type name: `specs::storage::MaskedStorage<rocket::entities::Ship>`', /home/yodalee/.rustup/toolchains/nightly-x86\_64-unknown-linux-gnu/lib/rustlib/src/rust/src/libstd/macros.rs:16:9  
```

這個原因是 component 內的 storage 要經過初始化才能使用，我們在 entity 裡面使用了 Ship 這個 component 卻沒初始化 storage，程式就爆掉了。  
register 就是向 world 註冊並初始化 component；未來我們加上 System 之後，只要有被 System 使用的 Component 都會自動初始化，這行就不需要了。  
不過我個人是建議有寫的 component 都把 register 留著，才不會修改 system 之後，程式突然就發生執行期錯誤。  
經過這麼一團千辛萬苦，現在執行起來就能看到飛船在中間的畫面了。  

![loadresource](/images/amethyst/resource.png)
