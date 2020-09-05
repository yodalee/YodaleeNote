---
title: "使用 Amethyst Engine 實作小行星遊戲 - 8 使用 ncollide2d 實作碰撞"
date: 2020-07-10
categories:
- rust
- amethyst
tags:
- rust
- amethyst
- ncollide
series:
- 使用 Amethyst Engine 實作小行星遊戲
---

碰撞偵測應該也是許多遊戲內必要的元素之一，比如說我們的打小行星遊戲，就需要偵測雷射砲跟小行星的碰撞，以及小行星和太空船的碰撞。  
簡單一點的土砲法，是用 for loop 把小行星跟電射砲的座標收集起來，太近的兩者把 entity 刪掉就行了；
但我們畢竟身為專業的遊戲設計（才怪），用土砲法就太遜了，這裡我們用同樣是 rust 寫的 [ncollide2d 套件](https://ncollide.org/)來實作碰撞偵測。  
<!--more-->

因為 amethyst 內部包了一層 nalgebra 的關係，我們的 ncollide2d 用的版本必須是 0.21 版，我覺得這個問題挺…麻煩的，
要自己去搜 amethyst 相依的 nalgebra 到底是哪個版本，然後對應回 ncollide2d 對應的版本。  
為了識別每一個物件的屬性，我們在各個 entity 上面都加上一個新的 component：Collider，內含一個 enum 屬性；在每個 entity 上面都要附上這個 component 作為識別。  
```rust
pub struct Collider {
  pub typ: ColliderType
}

pub enum ColliderType {
  Ship,
  Bullet,
  Asteroid,
}
```
從我們之前的教學文學到的 rule of thumb：

> 要改變行為，就是加一個系統。  

```rust
use ncollide2d::{
  bounding_volume,
  broad_phase::{DBVTBroadPhase, BroadPhase, BroadPhaseInterferenceHandler}
};
```
引入 ncollide2d 相關的模組。  

```rust
#[derive(SystemDesc)]
pub struct CollisionSystem;

impl<'s> System<'s> for CollisionSystem {
  type SystemData = (
    Entities<'s>,
    ReadStorage<'s, Collider>,
    ReadStorage<'s, Ship>,
    ReadStorage<'s, Transform>,
  );

  fn run(&mut self,
           (entities, colliders, ships, transforms): Self::SystemData) {

  // collect collider
  let mut broad_phase = DBVTBroadPhase::new(0f32);
  let mut handler = BulletAsteroidHandler::new();
  for (e, collider, _, transform) in (&entities, &colliders, !&ships, &transforms).join()  {
    let pos = transform.translation();
    let pos = Isometry2::new(Vector2::new(pos.x, pos.y), zero());
    let vol = bounding_volume::bounding_sphere( &Ball::new(5.0), &pos );
    broad_phase.create_proxy(vol, (collider.typ, e));
  }
  broad_phase.update(&mut handler);
```

新增一個 CollisionSystem，要動到有 Collider component 的 entity，讀位置需要 Transform。  

上面顯示了 ncollide2d 提供的 [DBVTBroadPhase](https://docs.rs/ncollide2d/0.21.0/ncollide2d/pipeline/broad_phase/struct.DBVTBroadPhase.html) 的碰撞偵測，它會把輸入的資料依照空間位置分到樹狀的結構上，更有效率的去偵測碰撞。  

用 for loop 把所有非 ship 的 collider 取出來，從 transform 建立物體位置，再建立 ncollide2d 提供圓形 `bounding_volume`，這是 DBVTBroadPhase 偵測用的 key。  
我們用 `(ColliderType, Entity)` 作為 value，ColliderType 是用來識別碰撞的物體型別，我們只希望偵測子彈跟小行星的碰撞，忽略其他像小行星自己的碰撞；Entity 則是在碰撞發生的時候，能夠追溯到是哪個 entity 發生碰撞。  

最後只要呼叫 DBVTBroadPhase 的 update 並代入實作 [BroadPhaseInterferenceHandler](https://docs.rs/ncollide2d/0.21.0/ncollide2d/pipeline/broad_phase/trait.BroadPhaseInterferenceHandler.html) 的 struct 即可。  

下面就來實作 handler：
```rust
struct BulletAsteroidHandler {
  collide_entity: Vec<Entity>,
}

impl BulletAsteroidHandler {
  pub fn new() -> Self {
    Self {
      collide_entity: vec![],
    }
  }
}

type ColliderEntity = (ColliderType, Entity);
```

定義一下 type alias 寫起來比較方便：  
```rust
impl BroadPhaseInterferenceHandler<ColliderEntity> for BulletAsteroidHandler {
  fn is_interference_allowed(&mut self, a: &ColliderEntity, b: &ColliderEntity) -> bool {
    a.0 != b.0
  }
  fn interference_started(&mut self, a: &ColliderEntity, b: &ColliderEntity) {
    self.collide_entity.push(a.1);
    self.collide_entity.push(b.1);
  }
  fn interference_stopped(&mut self, _a: &ColliderEntity, _b: &ColliderEntity) {}
}
```
* `is_interference_allowed` 用來判斷這兩個物體能不能發生碰撞，這裡要求它們的 ColliderType 要不一樣
* `interference_started` 則是碰撞發生時的處理，把兩個 entity 存進 collide_entity 裡面
* `interference_stopped` 處理碰撞結束的行為，留空就好  

上面呼叫完 `broad_phase.update(&mut handler)` 之後，從 `handler.collide_entity` 就能拿到碰撞的 bullet 跟 asteroid，刪掉 entity 即可。  

```rust
for e in handler.collide_entity {
  if let Err(e) = entities.delete(e) {
    error!("Failed to destroy collide entity: {}", e)
  }
}
```

這篇其實非常偷懶了，目前至少有下面兩點可以改進：  

*  不用在 system 裡面產生新的 DBVTBroadPhase 並重新插入 proxy  
應該把碰撞偵測當成一個 resource，每次只要更新 DBVTBroadPhase 內記錄的位置，速度應該會比我們這樣從頭打造一個快。

*  將 `bounding_volume` 存在 Collider 裡面，而不是每個東西都是單一尺寸的圓形  
這樣也不用每次都重新生成新的 `bounding_voluma`，從 Collider 裡面拿就可以了。

不過在我們這個小遊戲上還不需要在意這個，做完這一大步，現在遊戲已經有個可以玩的樣子了……

雖然我立刻發現它難度有點太高了，我通常撐不到十秒，~~放不出 C8763~~，不過這只需要我們動一些參數，最後再來調整就好了。  
