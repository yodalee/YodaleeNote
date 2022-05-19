---
title: "使用 Rust 實作 regular expression tester"
date: 2016-04-01
categories:
- rust
tags:
- rust
- understanding computation
series: null
---

其實這個功能很早以前就已經完成了，將正規表示式對轉換成Non-Deterministic Automata(NFA) ，來 match 字串，  
先前的實作有一些問題，因為再建 NFA的時候，狀態是使用整數來表示。  

在轉換成NFA時，正規表示式的 Concatenate, Choose, Repeat 需要將兩個NFA 結合成一個，因為由 Empty 或 Literal 直接建NFA時，
編號一定是從 0 開始，兩個都包含狀態 0 的狀態機，直接結合起來絕對不會是對的，需要讓兩邊的狀態都不一樣才行。  
當然也不可能用亂數來作為狀態，畢竟以亂數作為狀態，連一個NFA裡面有哪些狀態都不知道，結合時根本就無法檢查是否有衝突。  
<!--more-->

這是[之前版本的 toNFA](https://github.com/yodalee/computationbook-rust/blob/1c7177ca1be5ef914baf2acc7338da384d4257b6/the_simplest_computers/tonfa.rs)：  
```rust
use std::collections::HashSet;

use nfadesign::{NFADesign};
use nfarulebook::{NFARulebook};
use regex::{Regex};
use helper::{toHashSet};
use farule::{FARule};

pub trait ToNFA {
  fn to_nfa_design(&self) -> NFADesign;
  fn matches(&self, &str) -> bool;
}

impl ToNFA for Regex {
  fn to_nfa_design(&self) -> NFADesign {
    match *self {
      Regex::Empty => {
        NFADesign::new(
          0,
          &toHashSet(&[0]),
          &NFARulebook::new(vec![])
        )
      },
      Regex::Literal(c) => {
        NFADesign::new(
          0,
          &toHashSet(&[1]),
          &NFARulebook::new(vec![FARule::new(0, c, 1)])
        )
      },
      Regex::Concatenate(ref l, ref r) => {
        let first = l.to_nfa_design();
        let second = r.to_nfa_design();
        let start_state = first.start_state();
        let accept_state = second
          .accept_state()
          .iter()
          .map(|x| x+first.size)
          .collect::<HashSet<u32>>();

        let mut rule1 = first.rules();
        let mut rule2 = second.rules();
        for r in rule2.iter_mut() { r.shift(first.size) }

        let extrarule = first.accept_state()
          .iter().map(|state|
            FARule::new(*state, '\0', second.start_state()))
          .collect::<Vec<FARule>>();

        rule1.extend_from_slice(&rule2);
        rule1.extend_from_slice(&extrarule);

        NFADesign::new(
          start_state,
          &accept_state,
          &NFARulebook::new(rule1)
        )
      },
      Regex::Choose(ref l, ref r) => {
        let first = l.to_nfa_design();
        let second = r.to_nfa_design();
        let start_state = 0;
        let accept_state1 = first
          .accept_state()
          .iter()
          .map(|x| x+1)
          .collect::<HashSet<u32>>();
        let accept_state2 = second
          .accept_state()
          .iter()
          .map(|x| x+first.size+1)
          .collect::<HashSet<u32>>();
        let accept_state = accept_state1
          .union(&accept_state2)
          .cloned()
          .collect::<HashSet<u32>>();

        let mut rule1 = first.rules();
        for r in rule1.iter_mut() { r.shift(1) }
        let mut rule2 = second.rules();
        for r in rule2.iter_mut() { r.shift(1+first.size) }
        let extrarule = vec![FARule::new(0, '\0', 1),
                             FARule::new(0, '\0', first.size+1)];
        rule1.extend_from_slice(&rule2);
        rule1.extend_from_slice(&extrarule);

        NFADesign::new(
          start_state,
          &accept_state,
          &NFARulebook::new(rule1)
        )
      },
      Regex::Repeat(ref p) => {
        let pattern_nfa = p.to_nfa_design();

        let start_state = 0;
        let mut accept_state = pattern_nfa.accept_state()
          .iter().map(|x| x+1).collect::<HashSet<u32>>();
        let mut rules = pattern_nfa.rules();
        for r in rules.iter_mut() { r.shift(1) }

        rules.extend(accept_state
          .iter()
          .map(|x| FARule::new(*x, '\0', start_state)));
        rules.push(FARule::new(start_state, '\0', 1));

        accept_state.insert(start_state);

        NFADesign::new(
          start_state,
          &accept_state,
          &NFARulebook::new(rules)
        )
      },
    }
  }

  fn matches(&self, s: &str) -> bool {
    match *self {
      _ => self.to_nfa_design().accept(s)
    }
  }
}
```

可以看到因為使用整數來表示狀態，為了避免第二個NFA 接到第一個上面時，第二個NFA 的狀態和第一個的重複，必須實作一些必要的函式，例如：  
FARule 的 shift 將規則中的狀態都偏移一個數值；如果像 Choose 或 Repeat ，需要建一個新的start state，則兩個 NFA 的 rule都要shift；
另外像 accept state 也要用 iterator 的方式 shift，總之就是各種麻煩。  

相對的在書中的例子，使用Ruby實作的關係，他直接使用 Ruby Object 來當作他的狀態，絕對不會有重複的問題，就像這裡的start\_state：  
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
當然 Rust 也是可以這樣做，只是麻煩些，畢竟Ruby 是動態語言，要用什麼東西當狀態都可以直接使用，
Rust 需要明確的指定型別，某種程度它用 Ruby 實作也是一種語言的霸凌Orz。  

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
因為Rust 在struct 的比較的時候，會直接把struct 拆開比較裡面的值，所以上面 `start_state == next_state` 會是 true，
解決方法在於自己實做比較的方法，改成比較 struct 的位址即可避免不同 struct 被認定成相同：  

```rust
impl PartialEq for State {
    fn eq(&self, rhs: &Self) -> bool {
        self as *const _ == rhs as *const _
    }
}
```

另外 Rust 會避免同個 struct 被兩個不同的地方擁有，當我們使用了某個 State 當作 start\_state，我的rule 就沒辦法再用這個State 了，
上面的code 在建 NFA 的時候會報錯，因為 start\_state 跟 next\_state 已經move 到FARule 中了。  

因此我們狀態不能直接使用 state 而必須用 rust 的 [Reference Count: Rc](https://doc.rust-lang.org/std/rc/struct.Rc.html)。  

```rust
let start_state = Rc::new(State{});
let next_state = Rc::new(State{});
let rule = FARule(start_state.clone(), c, next_state.clone());
```

就可以避免重複使用start\_state 的問題，同時 start\_state == start\_state.clone() 也會是true。  

以下是[修改後的toNFA](https://github.com/yodalee/computationbook-rust/blob/904f02e1a9f51de684e1cac23c7d5707ce62c527/the_simplest_computers/regular_expressions/tonfa.rs)：  

```rust
use std::collections::HashSet;
use std::rc::Rc;

use nfadesign::{NFADesign};
use nfarulebook::{NFARulebook};
use regex::{Regex};
use helper::{toHashSet};
use farule::{State, FARule};

pub trait ToNFA {
    fn to_nfa_design(&self) -> NFADesign;
    fn matches(&self, &str) -> bool;
}

impl ToNFA for Regex {
  fn to_nfa_design(&self) -> NFADesign {
    match *self {
      Regex::Empty => {
        let start_state = Rc::new(State{});
        NFADesign::new(
          &start_state,
          &toHashSet(&[start_state.clone()]),
          &NFARulebook::new(vec![])
        )
      },
      Regex::Literal(c) => {
        let start_state = Rc::new(State{});
        let accept_state = Rc::new(State{});
        let rule = FARule::new(&start_state, c, &accept_state);
        NFADesign::new(
          &start_state,
          &toHashSet(&[accept_state]),
          &NFARulebook::new(
            vec![rule]),
        )
      },
      Regex::Concatenate(ref l, ref r) => {
        let first = l.to_nfa_design();
        let second = r.to_nfa_design();
        let start_state = first.start_state();
        let accept_state = second.accept_state();
        let mut rule1 = first.rules();
        let rule2 = second.rules();
        let extrarules = first.accept_state().iter()
          .map(|state| FARule::new(state, '\0', &second.start_state()))
          .collect::<Vec<FARule>>();
        rule1.extend_from_slice(&rule2);
        rule1.extend_from_slice(&extrarules);
        NFADesign::new(
          &start_state,
          &accept_state,
          &NFARulebook::new(rule1))
      },
      Regex::Choose(ref l, ref r) => {
        let first = l.to_nfa_design();
        let second = r.to_nfa_design();
        let start_state = Rc::new(State{});
        let accept_state = first
          .accept_state()
          .union(&second.accept_state())
          .cloned()
          .collect();
        let mut rules = first.rules();
        rules.extend_from_slice(&second.rules());
        rules.extend_from_slice(&[
          FARule::new(&start_state, '\0', &first.start_state()),
          FARule::new(&start_state, '\0', &second.start_state())]);
        NFADesign::new(
          &start_state,
          &accept_state,
          &NFARulebook::new(rules))
      },
      Regex::Repeat(ref p) => {
        let pattern_nfa = p.to_nfa_design();
        let start_state = Rc::new(State{});
        let mut accept_state = pattern_nfa.accept_state();
        accept_state.insert(start_state.clone());

        let mut rules = pattern_nfa.rules();
        rules.extend(accept_state
          .iter()
          .map(|state| FARule::new(state, '\0', &pattern_nfa.start_state())));

        NFADesign::new(
          &start_state,
          &accept_state,
          &NFARulebook::new(rules))
      },
    }
  }

  fn matches(&self, s: &str) -> bool {
    match *self {
      _ => self.to_nfa_design().accept(s)
    }
  }
}
```

相較起來簡單的多，也跟Ruby code 相似得多。
