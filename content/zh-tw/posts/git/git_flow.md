---
title: "Git-flow 簡介"
date: 2014-08-22
categories:
- git
tags:
- git
- gitflow
series: null
---

最近因為工作的關係接觸了git-flow相關的內容，在這裡就介紹一下git-flow的相關概念。基本上git-flow就是一個git 的擴展，把一群git 指令集合在一起，更方便管理人的操控，如果去看它的執行檔，其實就是一個shell script，所以使用git-flow時也可以用git 指令，同時只要熟練git的話，就算不用git-flow 也能操作自如。  

我認為git-flow最重要的還是背後那個分枝的規則，我覺得學起這個規則就好。
<!--more-->

我們就先討論它設計的理由，同時搭配相關的git 指令：  

git-flow會有五個主要的 branch:
* master
* develop
* feature
* release
* hotfix

以下一一介紹：  

## master
有master branch是當然的，master branch是要讓使用者使用的，使用者checkout project時就要看到的內容，master branch上的commit 應該加上tag表示軟體的版本。  
```shell
git tag -a v0.1 -m 'message here'
```

## develop
因為是要讓使用者用的，所以平時自然不能隨便在master 上面修修改改，開發者要先換個 develop branch上面進行開發。  
```shell
$ git checkout -b develop
or
$ git branch develop && git checkout develop
```

## feature
git 允許許多開發者一同開發這個project ，如果大家都一股腦往develop 上放東西，每個開發者都會被commit 時的衝突問題煩到死，因此要開發一個新的feature，就要新建一個feature 分枝。  
開發完時，這個分枝再併回develop 上：
```shell
$ git checkout -b feature-issue42
git commits
$ git checkout develop && git merge –no-ff feature-issue42
```
這個部分應該是最花時間的，通常會遇到共同開發的pull/push也是在這個部分，這裡不贅述，就請參考之前的文章[以pull request參與github專案開發]({{< relref "pull_request.md">}})：   

## release
軟體開發到一個程度，就進入release 流程，從develop 切換到release中，停止新增feature，開始專注在修bug 跟改文件等等工作上，準備就緒後，就外送到master 跟送回develop 中。  
```shell
$ git checkout develop && git checkout -b release
git commits (only bug fixes)
$ git checkout master && git merge --no-ff release
$ git tag add -v0.2 -m 'message here'
$ git checkout develop && git merge --no-ff release
```

## hotfix
最後，沒有軟體是沒問題的，如果master上被檢出需要立即修補的重大問題，這時就要動用hotfix，把master 分枝出hotfix branch，修完後再併入master 和develop中。  
```shell
$ git checkout master
$ git checkout -b hotfix
fix bugs, commit
$ git checkout master && git merge --no-ff hotfix
$ git tag -a 0.2.1 -m 'message here'
$ git checkout develop && git merge --no-ff hotfix
$ git branch -d hotfix
```

在文中的merge 指令都有使用 no fast-forwarding的--no-ff 指令，這是為了保留一個分枝跟合併的 記錄，以免fast-forwarding造成所有branch全混成一條。  
當然這個流程只是參考，事實上接觸的幾個project幾乎都沒有照這個流程，大部分都是把master當成文中的develop在用，一樣分出feature來開發但沒有release，然後hotfix branch就是用master一路往前修。  

所以說，感謝大家花了幾分鐘看了這篇廢文XDD 