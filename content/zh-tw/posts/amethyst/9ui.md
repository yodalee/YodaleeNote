---
title: "使用 Amethyst Engine 實作小行星遊戲 - 9 UI"
date: 2020-08-09
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

現在讓我們來建 UI，我覺得建 UI 是目前掌握度比較低的部分，我也在想怎麼做才是對的。  
本篇目標是加上一個計分用的文字：  
<!--more-->

首先是 resource 的部分，建立 FontRes 來保存載入的字型檔，要建立文字的時候只要取用這個資源即可：  
```rust
pub struct FontRes {
  pub font : FontHandle
}

impl FontRes {
  pub fn initialize(world: &mut World) {
    let font = world.read_resource::<Loader>().load(
      "font/square.ttf",
      TtfFormat,
      (),
      &world.read_resource(),
    );
    world.insert(
      FontRes { font : font }
    );
  }
  pub fn font(&self) -> FontHandle {
    self.font.clone()
  }
}
```

這部分跟載入 sprite 沒有差很多，就不贅述。  

另外我們再實作一個 ScoreRes，用來儲存目前的分數跟儲存 UI 文字的 Entity。  
```rust
pub struct ScoreRes {
  pub score: i32,
  pub text: Entity,
}

impl ScoreRes {
  pub fn initialize(world: &mut World) {
    let font = world.read_resource::<FontRes>().font();
    let score_transform = UiTransform::new(
      "score".to_string(), Anchor::TopRight, Anchor::MiddleLeft,
      -220., -60., 1., 200., 50.);
    let text = world
      .create_entity()
      .with(score_transform)
      .with(UiText::new(font, "0".to_string(), [0.,0.,0.,1.], 50.))
      .build();

    world.insert(ScoreRes {
      score: 0,
      text: text
    });
  }
}
```

簡單來說 UI 的文字，自然也是一個 entity，裡面有兩個 components 分別是位移 UiTransform 跟 UiText。

[UiTransform](https://docs.amethyst.rs/master/amethyst_ui/struct.UiTransform.html) 會需要幾個參數：  

* id ：幫助辨識是哪個 Ui 元件。
*  anchor、pivot：Ui 元素位在 parent 的哪個方位、位在自己的哪個方位，可以用九宮格的方式來指定。
*  後面五個數字則是指定 x, y, z, width, height。

這裡我們把顯示擊落數的文字定在畫面右上角，x y 的位移值剛好補償它的寬度跟高度。  

UiText 需要帶入剛剛讀進來的字型，後面指定文字內容、顏色跟尺寸。  

要修改文字的話，我們稍微修改一下先前實作的 Collision System，要新增存取 ScoreRes 這個 resource，
記得上面所說 UI 文字也是 entity，文字的資訊是保存在 UiText 這個 Component 裡面，所以要改文字，我們一併要存取 UiText 這個 Component：  
```rust
type SystemData = (
  WriteExpect<'s, ScoreRes>
  WriteStorage<'s, UiText>
)

fn run(&mut self,
          (mut scoretexts,
           mut uitext): Self::SystemData) {
  // change score
  scoretexts.score = scoretexts.score + 1;
  if let Some(text) = uitext.get_mut(scoretexts.text) {
    text.text = scoretexts.score.to_string()
  }
}
```
直接修改 resource 裡面儲存的 score 的值，再用 Component uitext 去取出 resource 裡記錄的 text entity，拿出來的就是 entity 所含的 UiText Component，這時候才能去修改它的 text 屬性。  

上面這段 code 我放在處理碰撞的地方，只要有雷射砲跟小行星碰撞就會執行一次，真的要分得非常詳細，可以把這段移到獨立的系統中，比較不會亂掉。  

你可能會問，這樣不就…讓 ScoreRes 這個 resource 的實作內容給暴露出來了，不能把 UiText 跟 score 等等的好好好封裝到一個 struct 裡面，並公開介面如 setText 讓外部使用嗎？  
沒錯當初我也是想要這樣設計，只不過到目前為止都沒有成功過 (.\_.)，目前只能將就一下用這樣難看的寫法，畢竟連官方的[範例](https://book.amethyst.rs/master/pong-tutorial/pong-tutorial-05.html#updating-the-scoreboard)
都是這樣教……如果有大大知道的話也請不吝賜教。  
