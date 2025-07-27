---
title: "使用 Amethyst Engine 實作小行星遊戲 - 10 暫停狀態"
date: 2020-09-28
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

因為搬家（詳見[上一篇]({{< relref "2020_blogger_to_hugo.md" >}})）的關係好久沒有更新了；現在搬完家終於可以回來繼續寫 amethyst 的文章啦，
現在寫文章插 code 根本是一種享受，跟 blogger 那種鳥編輯器完全不一樣。  
到目前為止，我們討論的範圍都不脫 ECS 的範疇，這兩章我們會實作更多有關 state 的部分，
我覺得寫到這邊我比較有感受到 amethyst 整體的架構是怎麼實作的，但也只是個人的感覺就是。

我們這章先來實作一個小小的功能，就是按下 esc 鍵的時候，能讓遊戲暫停下來，
對應 amethyst 的文件是第十章的 [controlling system execution](https://book.amethyst.rs/stable/controlling_system_execution.html)；
<!--more-->
文中建議了三個不同的寫法：
* [Custom GameData](https://book.amethyst.rs/stable/controlling_system_execution/custom_game_data.html)
* [State-specific Dispatcher](https://book.amethyst.rs/stable/controlling_system_execution/state-specific_dispatcher.html)
* [Pausable Systems](https://book.amethyst.rs/stable/controlling_system_execution/pausable_systems.html)

這裡面 Custom GameData 我試過但都沒有成功，Pausable Systems 沒有試，用 State-specific Dispatcher 成功實作，所以這裡就教這個作法。

還記得我們上次提到 state 是在[第一章]({{< relref "1setup.md">}})剛設定狀態的時候，
那時候就是宣告一個 struct 作為 state，所以這裡的第一步是把 Play State 跟 Pause State 分開，Pause State 比較簡單先看它：
```rust
use amethyst::{
  input::{VirtualKeyCode, is_key_down},
  prelude::*,
};

pub struct StatePause;
impl SimpleState for StatePause {
  fn handle_event(&mut self,
      _data: StateData<'_, GameData<'_, '_>>,
      event: StateEvent) -> SimpleTrans {
    if let StateEvent::Window(event) = event {
      if is_key_down(&event, VirtualKeyCode::Escape) {
        return Trans::Pop;
      }
    }

    Trans::None
  }
}
```

我們先宣告暫停用的 `StatePause`，所有的 State 可以分到獨立的檔案裡，會比較清楚，然後對 `StatePause` 實作 `SimpleState`，
`SimpleState` 可以實作的函式可見[參考文件](https://docs.amethyst.rs/stable/amethyst/trait.SimpleState.html)，
這裡只需要處理鍵盤事件，實作 `handle_event` 即可。  
後面就如上面所示，使用 is_key_down 跟 [VirtualKeyCode](https://docs.amethyst.rs/stable/amethyst_input/enum.VirtualKeyCode.html) 偵測 Escape 被按下，

按下時回傳一個 Trans::Pop 的 SimpleTrans，我們提過 amethyst 裡是用 stack 在儲存我們的設計遊戲進行時會處在 `StatePlay`，
按下 Escape 會將 `StatePause` 推入 stack 中，解除 Pause 只要把 `StatePause` Pop 掉就可以了。  
[SimpleTrans](https://docs.amethyst.rs/stable/amethyst/type.SimpleTrans.html) 是
 amethyst 提供 [Trans](https://docs.amethyst.rs/stable/amethyst/enum.Trans.html) 的簡化版本，
 使用預設的 StateData 跟 StateEvent，Trans 裡面有各種不同的 stack 操作，稍後實作更多 state 會用到其他操作，這裡只用到 None, Push 跟 Pop。

下一步來實作 `StatePlay`，因為要加 dispatcher 的關係，現在宣告要加上生命周期
（就是這個會讓 pretty-print 自動上色功能大混亂，讓我狠下心決定搬離 blogger XDD）：
```rust
#[derive(Default)]
pub struct StatePlay<'a, 'b> {
  pub dispatcher: Option<Dispatcher<'a, 'b>>,
}
```

後面我們要把所有在 `StatePlay` 會用到的 System 從 main 生成 `game_data` 那邊搬過來，本來的 main 大概是這樣：
```rust
let game_data = GameDataBuilder::default()
  .with_bundle(RenderingBundle::<DefaultBackend>::new()
  .with_bundle(TransformBundle::new())?
  .with_bundle(input_bundle)?
  .with_bundle(UiBundle::<StringBindings>::new())?
  // .with many system

let mut game = Application::new(assets_dir, StatePlay, game_data)?;
game.run();
```

現在我們要把上面註解的 system 都搬到 `StatePlay` 的 `on_start` 裡面，留在 `game_data` 裡的就只剩下連接輸入、繪圖、UI 等 bundle：
```rust
use amethyst::{
  core::ArcThreadPool,
  input::{VirtualKeyCode, is_key_down},
  prelude::*,
  shred::{Dispatcher, DispatcherBuilder},
};

impl<'a, 'b> SimpleState for StatePlay<'a, 'b> {
  fn on_start(&mut self, data: StateData<'_, GameData<'_, '_>>)
    let world = data.world;

    // initialize Resource
    // register Component
    // create dispatcher
    let mut dispatcher = DispatcherBuilder::new()
      .with(ShipControlSystem, "ship_control_system", &[])
      .with(PhysicalSystem, "physical_system", &["ship_control_system"])
      .with(BoundarySystem, "boundary_system", &["physical_system"])
      .with(SpawnAsteroidSystem::new(), "spawn_system", &[])
      .with(CollisionSystem, "collision_system", &[])
      .with(ExplosionSystem, "explosion_system", &[])
      .with_pool((*world.read_resource::<ArcThreadPool>()).clone())
      .build();
    dispatcher.setup(world);

    self.dispatcher = Some(dispatcher);
  }
```

在新版的 `on_start` 裡面，我們除了要初始化資源、加入物件之外，多出一步生成一個 dispatcher，然後把本來在 `game_data` 那邊的 system 一股腦全塞進去。  
`with_pool` 可有可無，預設 dispatcher 會產生一套自己的 thread pool，同時 amethyst 的主執行緒也會產生一個 thread pool ，
使用 `with_pool` 可以重用主執行緒的 thread pool （注意它也是一個 resource ArcThreadPool）可以節省資源。

```rust
fn update(&mut self, data: &mut StateData<GameData>) -> SimpleTrans {
  if let Some(dispatcher) = self.dispatcher.as_mut() {
    dispatcher.dispatch(&data.world);
  }
  Trans::None
}
```

有了 dispatcher 之後，再 `SimpleState` 的 update 函式裡面，呼叫 dispatch 函式，就會照著我們註冊系統的順序在每次更新時呼叫各 system 了；
而相對的 `StatePause` 裡面沒有註冊任何 system，因此一進入暫停狀態，所有的東西都會停止運作。  

最後 `StatePlay` 也需要偵測是否按下 Escape 鍵，`event_handle` 的實作跟 `StatePause` 的很像，但按下 escape 時要回傳 Trans::Push ，並把 `StatePause` 推入狀態的堆疊中：
```rust
fn handle_event(&mut self,
    _data: StateData<'_, GameData<'_, '_>>,
    event: StateEvent) -> SimpleTrans {
  if let StateEvent::Window(event) = event {
    if is_key_down(&event, VirtualKeyCode::Escape) {
      return Trans::Push(Box::new(StatePause));
    }
  }
  Trans::None
}
```

這樣我們就完成了 Play 跟 Pause 兩個狀態的實作，在遊戲中按下 escape，跳入暫停模式，會看到畫面上所有東西都停止運作；再按一下繼續遊戲。
