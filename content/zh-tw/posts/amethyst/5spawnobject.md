---
title: "使用 Amethyst Engine 實作小行星遊戲 - 5 生成物體"
date: 2020-07-01
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

其實這章才是真的讓這堆教學跟官方 pong 不一樣的地方，在遊戲內生成 entity；官方的 pong 就是生出兩塊板子一顆球，球跑到場外就計分然後把球放回場中間，完全不會新增/刪除 entity。  
<!--more-->

在這之前我們先做一點 refactor，之前我們在 states.rs 裡寫了一個函式：`load_sprite_sheet` 用來載入 sprite 資源，但這個資源沒向 world 註冊，在 system 裡面會無法使用。  
先來改善這點，把 `Handle<SpriteSheet>` 包進 struct，放到另一個 textures.rs 檔案裡：  
```rust
pub struct SpriteStore {
  handle: Handle<SpriteSheet>
}
```

這個 struct 提供兩個函式：  

*  `from_path`：利用 `load_sprite_sheet` 取得 `Handle<SpriteSheet>`，建構 SpriteStore
*  `sprite_render`：給定一個 `frame id` ，從 handle 建構出 `SpriteRender`。

另外一個新檔案則是 resources.rs：  
```rust
pub struct ShipRes {
  pub sprite_store: SpriteStore,
}

impl ShipRes {
  pub fn initialize(world: &mut World) {
    let sprite_store = SpriteStore::from_path(world, "ship");
    world.insert(
      ShipRes { sprite_store : sprite_store }
    );
  }

  pub fn sprite_render(&self) -> SpriteRender {
    self.sprite_store.sprite_render(0)
  }
}
```
用一個 struct 再把 `sprite_store` 包起來，我在名字後綴 Res 表示 Resource，用來跟 component 的 ship 做區隔，不然到處都是 Ship 很麻煩。  
這個 struct initialize 拿到 SpriteStore 後，會呼叫 `world.insert()` 把自己這個資源註冊到 world 裡面，使用同樣的結構，我們可以另外生成資源 BulletRes 用來生成子彈。  
記得在產生 game data 的時候，呼叫資源 struct 的 initialize 函式。  

現在我們可以擴充我們的 ShipControlSystem 了：  
```rust
impl<'s> System<'s> for ShipControlSystem {
  type SystemData = (
    WriteStorage<'s, Physical>,
    WriteStorage<'s, Ship>,
    ReadStorage<'s, Transform>,
    ReadExpect<'s, BulletRes>,
    Entities<'s>,
    Read<'s, LazyUpdate>,
    Read<'s, InputHandler::<StringBindings>>,
    Read<'s, Time>,
  );
```
擴充後的 SystemData 大幅增加取用的類別：  

* BulletRes 是 Resource，因為沒有 default 我們使用 ReadExpect 來讀取。
* Entities<'s>  新增/刪除 entity 必要的
* [LazyUpdate](https://docs.rs/amethyst/0.9.0/amethyst/ecs/prelude/struct.LazyUpdate.html) 是 amethyst 提供的一個方式  
如果一條更新會動到很多的資源，可以先用 LazyUpdate 的方式記下來之後一次處理。
* Time 跟 Ship 的寫入權限是要處理冷卻時間用的。

下面是在 ShipControlSystem 和射出子彈有關的原始碼：  
```rust
fn run(&mut self,
          (mut physicals,
           mut ships,
           transforms,
           bullet_resources,
           entities,
           lazy,
           input,
           time): Self::SystemData) {
  for (physical, ship, transform) in (&mut physicals, &mut ships, &transforms).join() {
    let shoot = input.action_is_down("shoot").unwrap_or(false);
    // handle shoot
    if ship.reload_timer <= 0.0f32 {
      if shoot {
        ship.reload_timer = ship.time_to_reload;

        let bullet_transform = transform.clone();
        let velocity = transform.rotation() * Vector3::y() * 150f32;
        let velocity = physical.velocity + Vector2::new(velocity.x, velocity.y);
        let bullet_physical = Physical {
          velocity: velocity,
          max_velocity: 200f32,
          rotation: 0f32,
        };

        let e = entities.create();
        lazy.insert(e, Bullet {} );
        lazy.insert(e, bullet_transform);
        lazy.insert(e, bullet_physical);
        lazy.insert(e, bullet_resources.sprite_render());
      }
    } else {
      ship.reload_timer = (ship.reload_timer - delta).max(0.0f32);
    }
  }
}
```

首先，在遊戲裡面會重複的只有 component，所以需要用 for loop 配 join 解開的也只有用 ReadStorage/WriteStorage 拿進來的 component，其他都不用。  

接著我們會去檢查 ship component 儲存的 `reload_timer`，依照 Time delta 減少，變為 0 就可以射擊，一但射擊了就會把 `reload_timer` 加一個冷卻時間。  
後面會用 ship 的 transform 算出子彈速度，產生子彈用的 physical component。  
產生 entity 其實很簡單，呼叫 `entities.create()` ，再用 LazyUpdate insert，往這個 entity 裡面塞 component。  
`bullet_transform` 跟 physical 都是我們剛產生的；resource 一定要先註冊過之後，才能像這樣用 ReadExpect 拿出來用，我們直接呼叫 `sprite_render` 函式，拿到可顯示的 SpriteRender component，一樣塞進去就行了。  

用 system 產生 entity 就介紹到這邊，其實沒有很難；大家應該更能感受到 ECS 系統的精神，Entity - 我們在螢幕上面看到的船 - 其實就是個空殼。  

*  它為什麼可以顯示東西？我們幫他加上一個 SpriteRender component。
*  它為什麼有速度可以旋轉？它有 physical component。
*  要變化位置？加上 transform component ，讀取 physical 來更新它。
*  要設定加速度的值？把加速度存在 ship component 裡。

沒錯，所有的東西都是 component 達成的，entity 一點用也沒有，隨之而來的就是彈性。  
還要加上碰撞？在需要碰撞的三個東西：船、小行星、雷射加上一個新的 Collider component ，再寫新的系統處理它就可以了，舊有的程式碼完全不需要改動，這大概是 ECS 系統帶來的最大好處了。  
