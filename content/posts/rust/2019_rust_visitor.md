---
title: "把一顆樹寫出來是會有多難"
date: 2019-11-16
categories:
- rust
tags:
- rust
- c
- design pattern
series: null
---

故事是這樣子的，之前小弟發下豪語想用 Rust PEG 寫一個 C Parser，然後…就沒有然後了。  
好啦當然不是，不然就不會有這篇文了。  

總之最近經過一陣猛烈的攪動之後，我的 parser 能處理的文法終於接近當年在學校修 compiler 的時候所要求的 B language 了，
說來慚愧，當年寫 compiler 作業的時候 parser 只是裡面一個作業，要在 2-3 週裡面寫完的，結果現在搞半天寫不出個毛，
果然上班跟上學還是不一樣，在學校可以全心全意投入寫 code ，週末的時候還可以熬個夜把作業寫出來；現在上班白天要改公司的 code ，晚上回家累個半死不想寫 code 只想開卡車(欸。  

本篇講到的程式碼目前還沒推到遠端上，相關的程式碼可以參考：  
AST 的資料結構：[cast](https://github.com/yodalee/carbon/blob/master/src/ast/cast.rs)  
型別的資料結構：[ctype](https://github.com/yodalee/carbon/blob/master/src/ast/ctype.rs)  
既然現在可以處理比較複雜的文法了，再來要做什麼？  

想說就像作業的要求一樣，把我們處理好的 AST 用 graphviz 寫出去，是會有多難？  

整個 dump graphviz 的進入點是一個函式，接收要倒出來的 AST 跟一個 out，out 的型別是 std::io::Write 的 dyn Write，
這樣不管你是要寫到 stdout, stderr 還是寫到檔案都能傳進來，介面會是一樣的，函式的實作當然就是直接了當的把該印的東西都寫出去；
另外實作一個 dump\_node 幫我們把寫出一個 node 給獨立出來，id 會自動不斷累加，讓 node 的編號不會重複。  
```rust
fn dump_graphviz(ast: CastTop, out: &mut dyn Write) {
    writeln!(out, "Digraph AST").unwrap();
    writeln!(out, "{{").unwrap();
    writeln!(out, "label = \"AST_Graph.gv\"").unwrap();
    writeln!(out, "node{} [label = \"PROGRAM_NODE\"]", 0).unwrap();
    ast.make_node(out, &mut 0);
    writeln!(out, "}}").unwrap();
}
fn dump_node(out: &mut dyn Write, id: &mut u32, label: &str) {
    *id += 1;
    writeln!(out, "node{} [label = \"{}\"]", id, label).unwrap();
}
```

另外我們要實作的是 make\_node，這裡很自然的就是先宣告一個 trait，AST 裡面所有的物件都要實作這個 trait ，就都有 make\_node 可以用了。  
```rust
trait ToGraphviz {
  fn make_node(&self, out: &mut dyn Write, id: &mut u32);
}

impl ToGraphviz for CastTop {
  fn make_node(&self, out: &mut dyn Write, id: &mut u32) {
    match self {
      CastTop::FuncDeclList(v) => {
        let cur_id = *id;
        for decl in v {
          dump_node(out, id, "DECLARATION_NODE FUNCTION_DECL");
          decl.make_node(out, id);
        }
        if *id != cur_id { // new node
          writeln!(out, "node{} -> node{} [style = bold]", cur_id, cur_id + 1).unwrap();
        }
      },
    }
  }
}

impl ToGraphviz for FuncDecl {
  fn make_node(&self, out: &mut dyn Write, id: &mut u32) {
    let parent = *id;
    dump_node(out, id, &format!("IDENTIFIER_NODE {} NORMAL_ID", "int"));
    dump_node(out, id, &format!("IDENTIFIER_NODE {} NORMAL_ID", self.fun_name));
    dump_node(out, id, "PARAM_LIST_NODE");
    dump_node(out, id, "BLOCK_NODE");

    for i in parent..*id {
      writeln!(out, "node{} -> node{} [style = {}]",
          i, i+1, if i == parent {"bold"} else {"dashed"}).unwrap();
    }
  }
}
```
註：本來的作業要求連結第一個 child 的必須是實線，其他的用虛線，這裡沿用  

這個實作的問題顯而易見，我們的輸出的實作跟資料綁死了，所以每個 node 裡面的實作都是大費周章，而且 code 很醜。  
我們要更抽象化一點，其實輸出樹的邏輯是這樣子的：先寫 child 的 node，然後是自己，回傳自己的 id 給 parent，這樣上一層的人才能畫 edge 出來。  
我們實作一個 dump\_children 的函式，這個函式會用現在的 id 印出現在的 parent，然後把它跟所有傳進來的 children 畫線連起來：  
```rust
fn dump_children(out: &mut dyn Write, id: &mut u32, label: &str, children: &[u32]) -> u32 {
  writeln!(out, "node{} [label = \"{}\"]", id, label).unwrap();
  let mut prev = *id;
  for child in children {
    writeln!(out, "node{} -> node{} [style = {}]", prev, child,
        if prev == *id { "bold" } else { "dashed" }).unwrap();
    prev = *child;
  }
  *id+=1;
  *id-1
}
```
因為 Rust 函式參數沒有預設值也沒有 overload，為了方便我們可以創一個 dump\_nochild 的函式，這樣比較方便：  
```rust
fn dump_nochild(out: &mut dyn Write, id: &mut u32, label: &str) -> u32 {
  dump_children(out, id, label, &[])
}
```
現在 make\_node 的實作都可以用 dump\_children 或 dump\_nochild 實作，先對自己的 child 們呼叫 make\_node，把回傳值（也就是 child 們印完的 root）收集起來再用 dump\_children 印出去就行了：  
```rust
impl ToGraphviz for CastTop {
  fn make_node(&self, out: &mut dyn Write, id: &mut u32) -> u32 {
    match self {
      CastTop::FuncDeclList(v) => {
        let children : Vec<_> = v.iter().map(|n| n.make_node(out, id)).collect();
        dump_children(out, id, "PROGRAM_NODE", &children);
      },
    }
    *id
  }
}

impl ToGraphviz for FuncDecl {
  fn make_node(&self, out: &mut dyn Write, id: &mut u32) -> u32 {
    let children = [
      dump_nochild(out, id, "IDENTIFIER_NODE int NORMAL_ID"),
      dump_nochild(out, id, &format!("IDENTIFIER_NODE {} NORMAL_ID", self.fun_name)),
      dump_nochild(out, id, "PARAM_LIST_NODE"),
      dump_nochild(out, id, "BLOCK_NODE")];
    dump_children(out, id, "DECLARATION_NODE FUNCTION_DECL", &children)
  }
}
```

這樣看起來就好多了，不過我們還能更進一步，仔細觀察上面的 dump\_children 的話，就會發現我們還能用 fold 的方式改寫：  
```rust
// print node, and link with all children
fn dump_children(out: &mut dyn Write, id: &mut u32, label: &str, children: &[u32]) -> u32 {
  *id+=1;
  writeln!(out, "node{} [label = \"{}\"]", id, label).unwrap();
  children.iter().fold(*id, |mut prev, child| {
      writeln!(out, "node{} -> node{} [style = {}]", prev, child,
          if prev == *id { "bold" } else { "dashed" }).unwrap();
      prev = *child;
      prev});
  *id
}
```
老實說，每次我費了這麼大的工夫，把一堆本來很黃很暴力的 code 改簡單，變成最後那樣的很純很 Functional 的 code，
我都會在內心懷疑個 100 遍，費這麼大功夫是真的有比較快嗎？
當然在維護上可能會好一點，但 Rust compiler 能保證抽象化真的是零成本的嗎？這可能是值得好好討論的議題。  

每個函式都要帶著 out 跟 id 走，很不方便，用一個 struct 把它們裝起來：  
```rust
struct DumpGraphviz {
  out: Box<dyn Write>,
  id: u32
}
```
dump\_children 跟 dump\_nochild 變成 DumpGraphviz 的實作，介面變成：  
```rust
fn dump_children(&mut self, label: &str, children: &[u32]) -> u32
fn dump_nochild(&mut self, label: &str) -> u32
```
make\_node 的介面則是：  
```rust
fn make\_node(&self, visit: &mut DumpGraphviz) -> u32
```
整體就變得清爽多了。  

天底下沒有新鮮事，其實我就是在實作 visitor pattern，只是還沒把 visitor 整個抽出來讓不同的 visitor 可以在這上面實作。最後輸出的成品長這個樣子：  
![rust_tree](/images/posts/rust_tree.png)

我有個小小的體悟，就是寫程式不要妄想一步登天，除非如強者我同學 AZ 大大那樣一眼就把超大程式的架構都畫出來，而且實作起來都不會亂掉。  

我上一次的實作就是衝太快，翻著 C standard 想要一開始就照著 C standard 實作，然後文法寫得亂七八糟反而連簡單的文法都會大噴射無法處理；
與其如此，不如先支援基本的功能，等 parser 跟文法處理都完善之後再慢慢把其他功能加上去。  
我覺得用蓋房子比喻的話，寫大程式要像西敏寺那樣的大教堂一樣，先從一個功能完整的小教堂開始，
然後把小部分拆掉蓋個更大更豪華的（有看過一個動畫片在演示這個過程的，只不過沒有公開版）；
如果一次就想蓋個超大的教堂，最後可能弄成一團廢墟，連禮拜的功能都沒有。  