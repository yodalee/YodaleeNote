---
title: "把 NFA 轉成 DFA 這檔事"
date: 2018-07-27
categories:
- rust
tags:
- rust
series: null
forkme: computationbook-rust/blob/master/src/the_simplest_computers/finite_automata/nfasimulation.rs
---

故事是這樣子的，最近寫了一些跟 Regex 相關的程式碼，無意間發現我之前understanding computation 這本書的實作中，並沒有實作非確定有限自動機（下稱 NFA）轉成有限自動機（DFA）的程式碼。  
<!--more-->

所以說我們這次就來實作一下。  

概念很簡單，我們手上有一個 NFA，我們可以把這個 NFA 從開始狀態開始，將這個狀態可以接受的字元都走走看，把每一個字元輸入之後的狀態組合都記下來（因為是NFA，同時可以存在許多狀態上），
重複這個流程直到所有狀態組合都被記錄過之後， 就能產生對應的 DFA，這個新的 DFA 每一個狀態都會原本 NFA 狀態的組合。  
這也代表：其實 NFA 並沒有比 DFA 更「高級」的能力，一切都可以用 DFA 來完成，NFA 只是在表示跟建構上，比 DFA 方便一些而已。  

實作一樣使用 Rust 的實作，雖然說也只是照著書上的 ruby code 實作就是了。  
在這之前我們已經完成了 FARule, NFARulebook, NFA, NFADesign 等一系列的 struct ，用上了 Rust 的泛型，確保 FARule 可以接受任何型別作為狀態，
無論[是整數還是一個 struct]({{< relref "2016_rust_re.md">}})，這點很重要，這樣我們後面的修改都不用再擔心狀態型別的問題。  

首先我們先創了一個 NFASimulation 的 struct，把之前已經實作完成的 NFADesign 塞進去，並加上一個新的函式 to\_nfa\_with\_states，
接受一個 NFA 狀態為參數，產生一個以這個狀態為初始狀態的 NFA （一般 NFADesign 產生的 NFA 的初始狀態是固定的）。  

接著我們在 NFASimulation 實作兩個函式：next\_states 和 rule\_for：  

* next\_states 會拿到一個 NFA 狀態（`HashSet<T>`）跟一個字元，回傳的是接受這個字元之後 NFA 新的狀態，
注意所謂 NFA 的狀態意思是 DFA 下狀態的組合，因此型態是 `HashSet<T>`。
* rule\_for 參數是 NFA 狀態，嘗試 NFA 中所有可能的輸入字元，回傳從這個狀態出發，所有可能的規則（FARule）。

最後把上面兩個函式結合在一起，實作 discover\_states\_and\_rules 函式，拿到只有一個初始狀態的集合之後，先呼叫 rule\_for 得到所有從這個狀態出發的 rule，
將每個 rules 指向的狀態取出來；如果新的狀態集合是輸入狀態集合的子集，表示所有可能的字元輸入都不會得到新的狀態，我們就已經遍歷整個 NFA 了；
否則，再把這個狀態集合丟進 discover\_states\_and\_rules 裡面，遞迴直到收集到所有狀態為止。  

話是這麼說，但開始實作之後就遇上一個問題，NFA 狀態表示是 `HashSet<T>`，discover\_states\_and\_rules 的輸入就是 `HashSet<HashSet<T>>` （NFA 狀態的集合）；
但 Rust 並不支援 `HashSet<HashSet<T>>` 這樣的泛型，當我試著從 discover\_states\_and\_rules，
設定回傳型別是 `HashSet<HashSet<T>>` ，rustc 立刻就噴我一臉錯誤，rustc 預設並沒有 `HashSet<T>` 的雜湊方式，也因此無法把它作為 HashSet 的 key。  

當然這是有解法的，後來是參考了下面[這個連結](https://stackoverflow.com/questions/27828487/is-it-possible-to-use-a-hashset-as-the-key-to-a-hashmap)：  
不能直接使用 `HashSet<HashSet<T>>`，得先把 `HashSet<T>` 封裝起來，放到名為 StateSet 的 
[tuple struct](https://doc.rust-lang.org/1.9.0/book/structs.html#tuple-structs) 當中，
tuple struct 的角色就是單純的封裝，可以用 struct.0 取得第 0 個封裝的元素，也就是封裝的 `HashSet<T>`。  

如此一來我們就可以實作一個 `StateSet<T>` 使用的雜湊方式，說出來沒啥特別，就是把整個 set 裡面的元素拿出來再雜湊一遍就是了，下面是相關的實作：  
```rust
use std::hash::{Hash, Hasher}
impl<T: Eq + Clone + Hash + Ord> Hash for StateSet<T> {
  fn hash<H>(&self, state: &mut H) where H: Hasher {
    let mut a: Vec<&T> = self.0.iter().collect();
    a.sort();
    for s in a.iter() {
      s.hash(state);
    }
  }
}
```
將 `HashSet<T>` 封裝成 StateSet 之後，就能使用 `HashSet<StateSet<T>>` 表示 NFA 狀態的集合，從狀態集合到狀態集合的規則，也能用 `FARule<StateSet<T>>` 表示，這樣就能夠完成 discover\_states\_and\_rules 函式，其返回值是 (states, rules)，即型別 `(HashSet<StateSet<T>>, Vec<FARule<StateSet<T>>>)`。  

利用 discover\_states\_and\_rules 一口氣拿到一個 NFA 所有可能的狀態集合，還有對應的規則，就可以產生一個對應的 DFA。  
```rust
pub fn to_dfa_design(&self) -> DFADesign<StateSet<T>> {
  let start_state = self.nfa_design.to_nfa().current_state();
  let mut start_set = HashSet::new();
  start_set.insert(StateSet::new(&start_state));
  let (states, rules) = self.discover_states_and_rules(&mut start_set);
  let accept_state = states.into_iter()
    .filter(|state| self.nfa_design.to_nfa_with_state(&state.0).accepting())
    .collect();
  DFADesign::new(StateSet::new(&start_state), &accept_state, &DFARulebook::new(rules))
}
```
在寫這一段程式碼的時候，因為是看著書中的 Ruby 範例程式碼在寫， 其實有很多地方的程式碼還滿像的，例如在 discover\_states\_and\_rules 裡面，
除了在型別上面卡關非常久之外，其他語法跟 Ruby 幾乎沒有什麼差別，真不虧是Rust，也許該私下稱 Rust 為「強型別的 Ruby/Python 」XD。  

不過呢，在 `HashSet<HashSet<T>>` 的問題上面，還有例如將兩個 `HashSet<T>` union 起來上，還是被 rustc 嗆了非常久，
真的是深切體會 Python, Ruby 等等知名語言背後到底幫我們處理多少髒東西。  

這篇文章[相關的原始碼](https://github.com/yodalee/computationbook-rust/blob/master/src/the_simplest_computers/finite_automata/nfasimulation.rs)可見  

## 心得
1. 我真的覺得，寫 Rust 的話，一定要記得下個 :set matchpairs+=<:> 開啟 <> 的 match，不然看看上面那複雜的嵌套，眼睛直接花掉。  
2. 寫過 Rust 之後再寫 C++ ……，這又醜又囉唆的語言是哪裡冒出來的，超級不習慣，不過就我目前的一點…直覺，
我覺得 C++ 如果把過去的東西都拋掉，把 std、reference、smart pointer 用到極致，就會得到一個很像 Rust 但沒有 Rust 記憶體檢查等功能的語言。  
3. Rust 是世界上最好的程式語言。  
4. 頑張るビー （誤  
