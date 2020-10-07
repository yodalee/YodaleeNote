---
title: "使用 Amethyst Engine 實作小行星遊戲 - 11 事件"
date: 2020-10-07
categories:
- rust
- amethyst
tags:
- rust
- amethyst
series:
- 使用 Amethyst Engine 實作小行星遊戲
---

上一篇我們做了兩個 state：遊戲進行和暫停的 state，理論上整個遊戲還需要更多的 state：像是遊戲結束、遊戲選單等等，但在這之前我們要先介紹 amethyst 的 event channel。  
先前我們在 state 間切換是透過按下鍵盤的事件，但遊戲進行間可能有些場景的轉換是由遊戲內的事件發動的，
例如我們的太空船被隕石砸到，要從遊戲狀態切到遊戲結束，這時候就要透過 event channel 來發送事件了；
同時，用了 EventChannel 可以讓我們改寫一些之前的程式碼，把不同功用的程式分到不用的 system 裡，不用全塞在一起。
<!--more-->

這章的內容多半來自同類型，也是 amethyst 展示箱的遊戲 [Space Shooter](https://github.com/amethyst/space_shooter_rs/)，
畢竟[Event Channel 的文件](https://book.amethyst.rs/stable/concepts/event-channel.html)裡面，
沒有多加描述該如何正確使用 Event Channel，只能翻 code 學怎麼用。

## 使用 Event Channel 切換狀態

就從我們的 CollisionSystem 開始，請參考舊文，使用 DBVTBroadPhase 偵測是否有兩個物體相碰撞，只要下列幾個 step 即可：

引入需要的模組，前面兩個分別是遊戲核心，要控制狀態轉換，還有 event channel ；後面我們要切換到 Pause State，實作的這個 state 也要引入：
```rust
use amethyst::prelude::{Trans, TransEvent, GameData, StateEvent},
use amethyst::shrev::{EventChannel};
use crate::states::{AsteroidGamePause};
```

EventChannel 可以廣播事件到整個遊戲裡，只要實作了 `Send + Sync + 'static` 的東西皆可為事件，
CollisionSystem 的 SystemData 中，我們加上這個長得很可怕的東西：
```rust
impl<'s> System<'s> for CollisionSystem {
  type SystemData = (
    Entities<'s>,
    ReadStorage<'s, Collider>,
    ReadStorage<'s, Transform>,
    WriteExpect<'s, ScoreRes>,
    WriteStorage<'s, UiText>,
    Write<'s, EventChannel<TransEvent<GameData<'static, 'static>, StateEvent>>>,
    ReadExpect<'s, ExplosionRes>,
    Read<'s, LazyUpdate>,
  );
```
https://docs.rs/amethyst/0.9.0/amethyst/enum.StateEvent.html
執行的部分，一旦我們偵測到太空船和隕石的碰撞，就會往 event channel 送入一個 Transition 的事件，透過 lambda 跟 Box 包裝起來，用 single_write 寫入這個事件：

```rust
fn run(&mut self,
           (//other component
            mut trans_events): Self::SystemData) {
  // call DBVTBroadPhase to detect collision
  if handler.ship_hit {
    let trans = Box::new(move || Trans::Switch(Box::new(AsteroidGamePause)));
    trans_events.single_write(trans);
  }
```
很神奇的，我們這樣就完成了 state 的轉換，在太空船相撞的時候就會跳進 Pause State 裡。

## 使用 Event Channel 在 System 間溝通

Event channel 當然不止這個用途，Event Channel 其實是整個 amethyst 的基礎之一，在各系統間都可以用 Event Channel 串接。  
例如我們[之前實作的 Collision System](https://yodalee.me/2020/07/8ncollide/) ，把偵測碰撞、處理碰撞都寫在一起了，
這樣混雜當然不是好事，我們要加上新的行為時就會愈來愈難改動，
可以利用 Event Channel 將兩者分開，偵測碰撞把碰撞的 Entity 往 Event Channel 裡面塞；
處理碰撞的 system 從 Event Channel 裡面拿出 entity，執行對應的動作。

第一步要先製作傳送的內容物，我們稱作 CollisionEvent，需要傳送的東西只有 entity 一個：
```rust
pub struct CollisionEvent {
  pub entity: Entity,
}
```

先看傳送的部分，比較簡單，新的 CollisionSystem 修改一下，component 新增一個寫入 CollisionEvent 的 EventChannel，有東西碰撞往裡面塞就是了：
```rust
impl<'s> System<'s> for CollisionSystem {
  type SystemData = (
    // ...
    Write<'s, EventChannel<CollisionEvent>>,
  );
  fn run(&mut self,
            (entities,
             //...
             mut collision_channel): Self::SystemData) {
    // call DBVTBroadPhase to detect collision
    for e in handler.collide_entity {
      collision_channel.single_write(CollisionEvent::new(e));
    }
  }
```

新的系統命名為 `DeletionSystem`，這個 system 會複雜一點，在讀取 Event Channel 需要下面幾個步驟：
1. 建立了 event channel
2. reader 向它註冊拿到一個 `ReaderId`
3. 讀取的時候送進這個 `ReaderId`，用來追蹤你上次讀到哪裡

要注意的是 Event Channel 在所有註冊的 Reader 都讀取完之後，才會移除寫入的 Event，
所以只要有一個 Reader 沒有固定更新，Event Channel 就會記錄愈來愈多的 event，最後把記憶體吃乾抹淨~~就像 chrome 一樣~~。

```rust
#[derive(Default)]
pub struct DeletionSystem {
  event_reader: Option<ReaderId<CollisionEvent>>,
}
```

我們要在哪裡初始化這個 `event_reader` 呢（注意它是 Option，因為還沒註冊時當然還沒有 ReaderId）？需要多實作一個函式 setup。
```rust
impl<'s> System<'s> for DeletionSystem {
  fn setup(&mut self, world: &mut World) {
    Self::SystemData::setup(world);
    self.event_reader = Some(
      world
        .fetch_mut::<EventChannel<CollisionEvent>>()
        .register_reader()
    )
  }
}
```
setup 會在把系統加到 dispatcher 上時被呼叫，這時就會透過 `register_reader` 取得 ReaderId。  
（在這裡我真的很想吐槽一下…setup 這個函式會被呼叫這件事文件提都沒有提，到底寫文件的都在幹嘛）  
在系統內就可以用這個 ReaderId 去跟 EventChannel 拿出 entity 了。  

```rust
impl<'s> System<'s> for DeletionSystem {
  type SystemData = (
    Read<'s, EventChannel<CollisionEvent>>,
  );

  fn run(&mut self,
            (collision_channel): Self::SystemData) {
    for event in collision_channel.read(self.event_reader.as_mut().unwrap()) {
      // do the things to entity
    }
  }
}
```

在 amethyst 裡面 entity 只是一個標記，用來抓出相關的 component ，完全沒有任何資料在裡面，所以我們可以像這樣用 event channel 在 system 間傳送 entity；
如果是內含資料的物件，在 rust 嚴格的記憶體管理下，實作 event channel 很容易就變成惡夢一場。  

本文展示使用 EventChannel 來控制狀態的轉換，以及用 EventChannel 將不同功能的程式碼分到不同的 System 裡面，
下一章我們來多加幾個狀態，就能完成一款超級陽春的遊戲，也就準備迎來 amethyst 系列文的尾聲啦lol。  