---
title: "使用Rust 實作regular expression tester"
date: 2016-04-01
categories:
- rust
tags:
- rust
- understanding computation
series: null
---

其實這個功能很早以前就已經完成了，將正規表示式對轉換成Non-Deterministic Automata(NFA) ，來match字串，  

先前的實作有一些問題，因為再建 NFA的時候，狀態是使用整數來表示。  
在轉換成NFA時，正規表示式的 Concatenate, Choose, Repeat 需要將兩個NFA 結合成一個，因為由Empty 或Literal 直接建NFA時，
編號一定是從 0 開始，兩個都包含狀態 0 的狀態機，直接結合起來絕對不會是對的，需要讓兩邊的狀態都不一樣才行。  
當然也不可能用亂數來作為狀態，畢竟以亂數作為狀態，連一個NFA裡面有哪些狀態都不知道，結合時根本就無法檢查是否有衝突。  
<!--more-->

這是之前版本的 toNFA：  
[toNFA with u32](https://github.com/yodalee/computationbook-rust/blob/1c7177ca1be5ef914baf2acc7338da384d4257b6/the_simplest_computers/tonfa.rs)  

可以看到因為使用整數來表示狀態，為了避免第二個NFA 接到第一個上面時，第二個NFA 的狀態和第一個的重複，必須實作一些必要的函式，例如：  
FARule 的shift 將規則中的狀態都偏移一個數值；如果像Choose 或Repeat ，需要建一個新的start state，則兩個 NFA的 rule都要shift；
另外像accept state也要用iterator的方式 shift，總之就是各種麻煩。  

相對的在書中的例子，使用Ruby實作的關係，他直接使用Ruby Object來當作他的狀態，絕對不會有重複的問題，就像這裡的start\_state：  
```ruby
class Choose
  def to_nfa_design
    first_nfa_design = first.to_nfa_design
    second_nfa_design = second.to_nfa_design
    start_state = Object.new
    accept_states = first_nfa_design.accept_states + second_nfa_design.accept_states
    rules = first_nfa_design.rulebook.rules + second_nfa_design.rulebook.rules
    extra_rules = [first_nfa_design, second_nfa_design].map { |nfa_design|
      FARule.new(start_state, nil, nfa_design.start_state)
    }
    rulebook = NFARulebook.new(rules + extra_rules)
    NFADesign.new(start_state, accept_states, rulebook)
  end
end
```
當然Rust 也是可以這樣做，只是麻煩些，畢竟Ruby 是動態語言，要用什麼東西當狀態都可以直接使用，Rust 需要明確的指定型別，某種程度它用Ruby 實作也是一種語言的霸凌Orz。  

相對應的修改如下：  
首先我們先建一個空的state，裡面不用內容，功用就跟Ruby 的Object 差不多：  
```rust
Struct State;
```
這樣就可以建state了：   
```rust
let start_state = State{};
let next_state = State{};
let rule = FARule(start_state, c, next_state);
NFA(start_state, next_state, rule);
```
因為Rust 在struct 的比較的時候，會直接把struct 拆開比較裡面的值，所以上面 `start_state == next_state` 會是true，
解決方法在於自己實做比較的方法，改成比較struct 的位址即可避免不同struct 被認定成相同：  
```rust
impl PartialEq for State {
    fn eq(&self, rhs: &Self) -> bool {
        self as *const _ == rhs as *const _
    }
}
```

另外 Rust 會避免同個struct 被兩個不同的地方擁有，當我們使用了某個State當作start\_state，我的rule 就沒辦法再用這個State 了，
上面的code 在建nfa 的時候會報錯，因為start\_state 跟next\_state 已經move 到FARule 中了。  

因此我們狀態不能直接使用 state 而必須用 rust 的 [Reference Count: Rc](https://doc.rust-lang.org/std/rc/struct.Rc.html)。  
用Rc<State> 當作state，這樣  
```rust
let start_state = Rc::new(State{});
let next_state = Rc::new(State{});
let rule = FARule(start_state.clone(), c, next_state.clone());
```
就可以避免重複使用start\_state 的問題，同時 start\_state == start\_state.clone() 也會是true。  

以下是修改後的toNFA：  
[toNFA with struct state](https://github.com/yodalee/computationbook-rust/blob/904f02e1a9f51de684e1cac23c7d5707ce62c527/the_simplest_computers/regular_expressions/tonfa.rs)  
相較起來簡單的多，也跟Ruby code 相似得多。