---
title: "使用 Amethyst Engine 實作小行星遊戲 - 12 更多的狀態"
date: 2020-10-09
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

這章我們要一口氣新增兩個新的狀態：StateMenu 跟 StateOver，基本上因為不同的 state 都分到不同的檔案，所以多幾個 state 也沒差。  
這章其實沒有太多需要介紹的，只有在 state 轉換上面多費點功夫，這部分可以先畫一個狀態圖讓整體更清楚：  
![stateflow](/images/amethyst/stateflow.png)
<!--more-->

amethyst 在[狀態間切換 Trans](https://docs.rs/amethyst/0.9.0/amethyst/enum.Trans.html) 共有幾個不同的方式：
* None：什麼事都不做
* Pop：從 stack 踢出一個 state
* Push：往 stack 塞入一個 state
* Switch：踢掉現在的 state，塞入一個新的 state
* Quit: 清空所有的 state，等於是結束遊戲的應用程式

與之對應的，在我們[實作各 state ](https://docs.amethyst.rs/stable/amethyst/trait.SimpleState.html)的時候，要實作對應的函式：
* on_start：狀態開始的時候執行，通常要初始化狀態內的各個資料，初始化資源。
* on_stop：狀態結束的時候執行，清除初始化的資源。
* on_pause：當一個新的狀態 push 進來，壓到現在狀態的頭上時執行。
* on_resume：當應用程式回到這個狀態時執行。

下面就概敘一下各 state 的實作內容 ：

### StateMenu
* on_start：初始化所有的 resource，太空船、隕石、雷射的 sprite；字體、亂數；註冊所有 component；加上相機；顯示 menu 文字。
* on_pause：移除 menu 文字。
* on_resume：顯示 menu 文字。
* handle_event：偵測鍵盤事件，按下 space 進入 StatePlay；按下 ESC 的時候會送出 Trans::quit 讓遊戲直接結束。
StateMenu 沒有實作 on_stop，因為它就是基底了。

### StatePlay
* on_start：加上太空船，註冊所有 system 到 dispatcher 裡。
* update：如同我們在[暫停狀態]({{< relref "10pause.md">}})那章所見，使用 dispatcher 之後要自行在 update 裡面呼叫 dispatch 函式。
* handle_event：按下 ESC 則是由 `handle_event` 進到 StatePause。
在太空船被隕石砸到的時候，會由 system 將狀態 switch 到 StateOver。

### StatePause
這個只是個空狀態，只要實作 `handle_event` 處理按下 ESC 的事件即可。

### StateOver
* on_start：顯示文字
* on_stop：刪除所有除了 Camera 以外的 entity，在遊戲狀態從 Play 切換到 Over 時，我們並沒有刪除 entity，所以東西都會留在畫面上靜止不動。
這裡的寫法是這樣：
```rust
fn on_stop(&mut self, data: StateData<'_, GameData<'_, '_>>) {
  let world = data.world;
  world.exec(|(entities, cameras) : (Entities, ReadStorage<Camera>)| {
    for (e,_) in (&entities, !&cameras).join() {
      if let Err(e) = entities.delete(e) {
        log::error!("Failed to destroy entity: {}", e);
      }
    }
  });
}
```
也就是說，world.exec 會收一個 lambda，這個 lambda 的寫法就跟平常寫 system 時沒什麼兩樣，參數就是各資源及 component；
或者也可以直接呼叫 `world.delete_all()` 把所有東西都刪光，但這樣在 StateMenu 的 on_resume 就要再一次初始化 camera，比較沒這麼漂亮。

還有一個提一下，如果有想要在不同的 State 間共用的資料（在我的遊戲裡是隕石擊墜數），基本上就要放在 resource 裡面，透過 read_resource 把它讀出來即可，
就如我們在 [UI 那章]({{< relref "9ui.md">}})實作了 ScoreRes，在 StateOver 的時候用 read_resource 就可以取出內存的 score 值了。
```rust
let score = world.read_resource::<ScoreRes>().score;
```

寫到這裡一個極簡（而且沒人想玩）遊戲就完成啦，但不管再怎麼複雜的遊戲，最基本用到的東西和這個簡單遊戲也相差無幾，就期待各位大展身手，用 amethyst 寫一個 3A 大作出來(欸。
