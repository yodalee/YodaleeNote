---
title: "使用 Amethyst Engine 實作小行星遊戲 - 7 亂數"
date: 2020-07-05
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

亂數在遊戲中也是個舉足輕重的腳角，少了亂數的遊戲就像沒加珍珠的奶茶(?，讓玩家食之無味；這章我們會加上亂數，以及產生小行星的 system。  
<!--more-->

亂數直接用 rust 官方的 rand 模組，為了把它嵌入 ECS 裡面，可以觀察一下亂數模組會有什麼特性：大家使用一個亂數模組而不是大家都有一份，符合這個特性的就是 resource 了。  

在 resources.rs 加上一個新的 struct：  
```rust
pub struct RandomGen;

impl RandomGen {
  pub fn next_f32(&self) -> f32 {
    use rand::Rng;
    rand::thread_rng().gen::<f32>()
  }
}
```
它把 rand 模組給包起來，在內部呼叫 thread\_rng().gen 產生 f32 的亂數，在載入資源的時候我們一併插入這個 resource。  
AsteroidRes 請仿造 ShipRes 跟 BulletRes 寫一份，這裡應該可以再把三個資源共用的部分抽出來，不過因為是範例 project 我就沒這麼做：  

```rust
ShipRes::initialize(world);
BulletRes::initialize(world);
AsteroidRes::initialize(world);
world.insert(RandomGen);
```

ECS 的道理，要加上新的行為就是寫一個新的系統，我們把和生成小行星有關的設定都放在這個系統裡面（雷射槍的冷卻時間和太空船是綁在一起的，因此放在 Ship component 裡面）：  
```rust
#[derive(SystemDesc)]
pub struct SpawnAsteroidSystem {
  pub time_to_spawn: f32,
  pub max_velocity: f32,
  pub max_rotation: f32,
  pub distance_to_ship: f32,
  pub average_spawn_time: f32,
}
```

實作上：  
* entities、LazyUpdate 是產生新物件必備
* Ship、Transform 用來取得船的位置，免得小行星直接出現在太空船的旁邊
* AsteroidRes、RandomGen 則是需要的資源：  

```rust
impl<'s> System<'s> for SpawnAsteroidSystem {
  type SystemData = (
    Entities<'s>,
    ReadStorage<'s, Ship>,
    ReadStorage<'s, Transform>,
    ReadExpect<'s, AsteroidRes>,
    ReadExpect<'s, RandomGen>,
    Read<'s, LazyUpdate>,
    Read<'s, Time>,
  );

  fn run(&mut self,
    (entities,
     ships,
     transforms,
     asteroidres,
     rand,
     lazy,
     time): Self::SystemData) {
  let delta = time.delta_seconds();
  self.time_to_spawn -= delta;

  if self.time_to_spawn <= 0.0f32 {
      // other code
  }

```

一開始就跟 ShipControlSystem 一樣，從 `time.delta_seconds` 取得秒數，去扣掉 system 的 `time_to_spawn`，一但低於零就會生成一顆小行星，並將 `time_to_spawn` 設定回 `average_spawn_time`。  
```rust
let mut create_point: Vector3<f32> = zero();
// generate creation point
loop {
  create_point.x = rand.next_f32() * ARENA_WIDTH;
  create_point.y = rand.next_f32() * ARENA_HEIGHT;
  if (ship_translation-create_point).norm() > self.distance_to_ship {
    break;
  }
}
transform.set_translation_x(create_point.x);
transform.set_translation_y(create_point.y);
```

生成點的位置我用了偷懶的方式，一般在 system 內最好不要有這種執行時間不確定的東西，如果一不小心 `distance_to_ship` 設太大，可能會讓 system 進到無窮迴圈把整個遊戲卡住，比較好的做法應該是從 `distance_to_ship`，亂數產生距離跟方位角就可以了。  
```rust
let e = entities.create();
lazy.insert(e, Asteroid {} );
lazy.insert(e, transform);
lazy.insert(e, physical);
lazy.insert(e, asteroidres.sprite_render());

self.time_to_spawn = self.average_spawn_time + rand.next_f32();
```
所有的 component 都準備好之後，一樣透過 LazyUpdate 把 component 塞進 entity 裡面即可，
另外也要記得重設 `time_to_spawn` 的值。

現在我們的遊戲應該有個樣子，平均每兩秒生成一顆小行星，按空白可以射出雷射。  
我們還沒實作碰撞，所以自然還沒有任何打爆小行星的行為，雷射打到小行星也只是無視的飛過去，下一章我們就進到一般遊戲除了亂數之外另一個必備成員：碰撞。  
