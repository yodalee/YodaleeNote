---
title: "使用git squash 合併commit"
date: 2014-04-14
categories:
- git
tags:
- git
series: null
---

小弟之前一直有個習慣，每次寫程式都要寫到結果正確了，才把該commit的commit；這樣造成的結果是，常常累積了數百行的差異才commit，要是中途不小心手滑了一下，辛苦就全化作流水了。  
> 阿蹦大神曰：不用結果正確，編譯可過就commit  

這樣…不是會跑出一堆亂七八槽的commit嗎？  
這就要用到git squash功能了。  
<!--more-->

比如說現在我隨便commit一些版本，log顯示為：  
```txt
commit 7549a19b591f1c802addf9b2344be2f607beff42  
Date: Mon Apr 14 16:05:38 2014 +0000  

more line num  

commit a15d1dde304646d542dc9cb596afbcd900a609c7  
Date: Mon Apr 14 16:05:22 2014 +0000  

line num  

commit 265e09db81b1c6aff81a6bedcd3a0e2f22e55acc  
Date: Mon Apr 14 16:04:49 2014 +0000  

initial commit  
```

如果要合併line num, more line num兩個版本：   

```shell
$ git rebase -i 265e09db81b1c6aff81a6bedcd3a0e2f22e55acc   
```

然後編輯將  
```txt
pick a15d1dd line num  
pick 7549a19 more line num  
```
要squash起來的commit編輯 為squash (s) , 或ffixup (f)，前者會保留 squash的commit message，後者只用最新的 commit message，先改成：  
```txt
pick a15d1dd line num  
squash 7549a19 more line num  
```

再來它會要求你修改commit message，這就隨便你改，預設是把兩個訊息寫在一起。  

如此一來兩個 commit 就被合併起來了：  
```txt
commit 0a947a06fd258e07615fb236696b8f31f04f4043  
Date: Mon Apr 14 16:05:22 2014 +0000  
line num  
more line num  

commit 265e09db81b1c6aff81a6bedcd3a0e2f22e55acc  
Date: Mon Apr 14 16:04:49 2014 +0000  

initial commit   
```

以後就寫個段落就commit一下，等到功能都寫完了，再全部 squash 起來即可。  

## 參考資料
man git rebase  

## 致謝
本文感謝傳說中的阿蹦大神指導