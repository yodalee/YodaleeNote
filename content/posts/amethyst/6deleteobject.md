---
title: "使用 Amethyst Engine 實作小行星遊戲 - 6 刪除物體"
date: 2020-07-03
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

一般來說這種射小行星的遊戲，都會有一個莫名的設定，那就是太空船和小行星來到邊界的時候，會從螢幕的對面出現，就好像畫面是一個攤平的球體一樣。  
<!--more-->
估且不論這個設定合不合理，我們就來實作一下：  

託 amethyst 之福，所謂實作就是：加一個新的 system，這裡叫它 BoundarySystem：  
```rust
#[derive(SystemDesc)]
pub struct BoundarySystem;

impl<'s> System<'s> for BoundarySystem {
  type SystemData = (
    WriteStorage<'s, Transform>,
    ReadStorage<'s, Physical>,
    ReadStorage<'s, Bullet>,
    Entities<'s>,
  );
```

這個 system 要改動的是所有含 Physical Component 的 entity 的 Transform 屬性，設定 Transform 為 Write；要刪除 entity 因此需要 Entities。  
```rust
for (_, _, transform) in (&physicals, !&bullets, &mut transforms).join() {
  let obj_x = transform.translation().x;
  let obj_y = transform.translation().y;
  if obj_x < 0.0 {
    transform.set_translation_x(ARENA_WIDTH-0.5);
  } else if obj_x > ARENA_WIDTH {
    transform.set_translation_x(0.5);
  }

  if obj_y < 0.0 {
    transform.set_translation_y(ARENA_HEIGHT-0.5);
  } else if obj_y > ARENA_HEIGHT {
    transform.set_translation_y(0.5);
  }
}
```

之所以要引入 bullets，是因為我們希望把含有 bullet component 一出畫面就直接消失，需要分出來特別對待。

在 for loop join 的地方，可以列出一排 component，取出「包含所有列出 component 的 entity」，也可以用 Logical negation operator !，取出「不包含這個 component 的 entity」，就可以把 bullet 給排除在外。  
```rust
for (e, _, transform) in (&*entities, &bullets, &mut transforms).join() {
  let x = transform.translation().x;
  let y = transform.translation().y;
  if x < 0.0 || y < 0.0 || x > ARENA_WIDTH || y > ARENA_HEIGHT {
    if let Err(e) = entities.delete(e) {
      error!("Failed to destroy entity: {}", e)
    }
    continue;
  }
}
```
另外一個迴圈處理 bullet，這次我們用 `&*entities` 拿到對應的 entity，在超出螢幕範圍的時候，呼叫 `entities.delete(e)` 把 entity 給刪除。  

其實刪除 entity 就是如此簡單，單獨成一章實在有點不平衡XD。  
