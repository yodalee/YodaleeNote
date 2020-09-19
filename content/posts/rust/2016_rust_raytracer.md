---
title: "用Rust 重寫 Raytracer From Scratch"
date: 2016-03-20
categories:
- rust
tags:
- rust
- raytracer
series: null
---

最近看到傳說中的jserv 大神所開的2016系統軟體課程，用C寫了一個Raytracing 的程式，就想我也用rust 也一遍，
<!--more-->
原本的作者是用 C++ 寫的，相關資源如下：  

* Youtube channel：  
{{< rawhtml >}}
<iframe width="560" height="315" src="https://www.youtube.com/embed/videoseries?list=PLHm_I0tE5kKPPWXkTTtOn8fkcwEGZNETh" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
{{< /rawhtml >}}

* [C++ source code]*(https://sourceforge.net/projects/rasterrain/):  
* [Rewritten in C](https://github.com/purpon/raytracing_c):  

這次決定全用cargo 的方式來維護我的project，第一步當然是先用cargo 產生project  
```bash
cargo new raytracing-rust –bin   
```
它會建好一個Hello world 的小程式，我們就從這個小程式一步一步往上加。  
用了cargo 的好處就是想要什麼，[crates.io](https://crates.io/) 上可能都有，例如我們要測量程式執行時間，只要在Cargo.toml 裡加上  
```toml
[dependencies]  
time = "0.1"   
```
主程式就可以加上：  
```rust
extern crate time;
use time::precise_time_ns;

let t1 = precise_time_ns;
let t2 = precise_time_ns;
```
即可使用相關的function ，跟C裡面 `#include<time.h>` 是類似的，只是cargo 會幫你管好相依的套件，執行cargo build 就行了。  

要寫入bmp 檔也是，完全不用手爆savebmp function，一樣加上  
```toml
[dependencies]
bmp = "0.1.4"
```
```rust
extern crate bmp;
use bmp::{Image, Pixel};
```

相當方便，最大的麻煩其實是crates 上面的文件有時候很少…根本是幾乎看不懂的地步，另外crates的碎片化也有點嚴重，
有些常用的模組有複數個可以選擇時，很可能根本不知道要選哪一個比較好。  

同樣道理，影片的4/9 有很大一塊被 nalgebra的Vec3 做掉，根本不用手爆Vect.h跟那一大串線性Vect 運算；顏色也是直接用crates.io palette 的Rgba，不造輪子了直接造車子去。  

寫的時候深覺Rust 的型別系統真的是嚴僅過剩，看看這段：   
```rust
let fx = x as f64;
let fy = y as f64;
if ASPECT > 1.0 {
    xamnt = ((fx+0.5)/FWIDTH)*ASPECT - ((FWIDTH-FHEIGHT) / FHEIGHT / 2f64);
    yamnt = ((FHEIGHT - fy) + 0.5)/FHEIGHT;
} else if ASPECT < 1.0 {
    xamnt = (fx+0.5)/FWIDTH;
    yamnt = (((FHEIGHT - fy)+0.5)/ FHEIGHT)/ASPECT - ((FHEIGHT-FWIDTH)/ FWIDTH/2.0);
} else {
    xamnt = (fx+0.5)/FWIDTH;
    yamnt = ((FHEIGHT - fy) + 0.5)/FHEIGHT;
}
```
FWIDTH跟FHEIGHT都是已經轉成f64 的width, height，Rust 在四則運算上，就限制了float 不能跟int, unsigned int 之類的運算，
你一定要自己轉型不然 rustc 就跟你該該叫。  

Rust 也能用一些相當高階的寫法，很多C/C++裡的index based for loop 在這裡都可以簡化
（當然這樣寫是不是比較快？有沒有必要這樣寫倒不一定），例如要求某個陣列中的最大值，如果是for loop 寫法會是這樣：  
```rust
let mut max = 0.0f64;
for intersect in intersections.iter() {
    if *intersect > max {
        max = *intersect
    }
}
```
但我們可以改成一行文：  
```rust
let mut max = intersections.iter().fold(0.0f64, |max, &x| x.max(max));
```

又或者，下面是對所有物件呼叫它的findIntersection() 函數，並尋找其中是否有物件有交點，與交點的距離又要小於和光源的距離，正規方式先建Vec，再去Vec中尋找：  
```rust
let mut second_intersect :Vec = Vec::new();
for obj in scene_obj.iter() {
    second_intersect.push(obj.findIntersection(&shadow_ray));
}
for d in second_intersect {
    if d > ACCURACY && d <= light_dis {
        // object between light and intersect point
        shadowed = true;
        break;
    }
}
```
但我們可以省下建Vec的步驟，直接用迭代的方式：  
```rust
let shadowed = scene_obj
    .iter()
    .map(|x| x.findIntersection(&shadow_ray))
    .any(|x| x>ACCURACY && x< light_dis);
```
當然我得承認我功力不到家，這份main.rs裡面有很多地方混合了迭代器的寫法跟index based 的寫法，看起來整個很怪。  

不過會動啦，以下是輸出的圖：  
![ball](/images/posts/scene.png)

整體的code 323行，和C version 1500行比起來短小精悍得多(當然我有很多功能還沒有實作就是了)；
執行時間的話，我用rust time 去算執行時間是 0.08，雖然C version 是1.53s，但考量它有開AA，可能讓運算量倍數成長，就先不去考慮效率不效率了  

## 結語  
其實某種程度上這也是興趣使然而寫的，也算當做練習Rust，我覺得寫Rust 有個要點要把握，能找到crates 就用，不要沒事就鑽下去認真打造基礎零件，在這個上面認真你就輸了。  

其實我這個也可以算重造輪子，拔拔你看[人家造的車子](https://github.com/gyng/rust-raytracer)都已經上太空啦~~  

原始碼都[放在這裡](https://github.com/yodalee/Raytracing-rust)，歡迎大家來fork:  

## 後記  
* 寫這個就會覺得我當初3DMM 沒學好，對不起簡教授QAQ  
* 算是小小吐槽一下好了，原本的那部影片用的根本是用了 Class 跟 Vector 的 C  
我邊看邊Murmur: 你這樣寫你到底會不會寫C++ 呀幹 然後有些地方的寫法，例如它Sphere 的findIntersection()，
把各個vector 翻出來開腸剖肚的寫法，你真的有想過這些東西都是向量運算，之前你就實作過了，你寫了20 行的東西我兩行就寫完了耶XD