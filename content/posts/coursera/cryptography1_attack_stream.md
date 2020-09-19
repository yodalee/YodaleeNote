---
title: "Cryptography 1：攻擊stream cipher "
date: 2015-09-17
categories:
- coursera
- cryptography
tags:
- coursera
- cryptography
series: null
---

密碼學中，有一種極簡的密碼，就是stream cipher(流加密XD)，對各式的明文，隨機產生一組和它一樣長的 key 並和明文 xor 起來，就是一個夠好的加密，只要該密鑰是隨機產生，如同[上一篇]({{< relref "cryptography1_random.md">}})所說，密文也會夠隨機。  
在實務上，通常不會用真的 random 密鑰，因為這會讓密鑰的長度要跟訊息一樣長，不實用，你能想像要先交換一組GB等級的密鑰嗎？我們會用pseudorandom generator，把短密鑰生成為長密鑰，來解決這個問題。  
<!--more-->
註：事實上我是聽課才知道這種加密，不像強者我同學曾奕恩大大，完全無師自通，看來我該讓賢了。  

這個加密系統有一大弱點，就是密鑰是一次性的，若一把密鑰重覆使用，而密文遭人攔截，則攻擊者可以利用：  
```txt
c1 ⊕ c2 = (m1 ⊕ k) ⊕ (m2 ⊕ k) = m1 ⊕ m2
```
若明文是以 ASCII 儲存，`m1 ⊕ m2` 已經有足夠資訊讓人猜出內容。  

例如，明文常有的space，ascii 是0x20或32，它跟英文字母xor 起來的結果，大多會落在大小寫轉換的英文字母範圍內，我們用python 來試試：  
```python
uppercase = list(range(65,91))
lowercase = list(range(97,123))
msg = uppercase + lowercase
print("".join([chr(c ^ 32) for c in msg]))
print("".join(chr(c) for c in msg))
```
會得到：  
```txt
abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ
ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz
```
其實它X的根本就是一個對上一個，這和一般最可能發生的字母 xor 字母產生的結果相差頗大，例如 a xor z = 27 還在不可視字元範圍內，所以如果xor 的結果落在字母內，很可能表示c1, c2中有space。  
我們可以先產生一個字典，以常用ASCII 和space xor的結果為鍵，以便用來反查該ASCII 的值：  
```python
xorSpace = {}
for c in msg:
    xorSpace[c^32] = c
```
然後對各截到的密文，假設是c0, c1 … cn，c0 xor c1 中存在字典中的字元位置，就有可能是c0或c1在這裡有space，將這些位置存下來，跟c0, c2 有space 位置取交集，就能得到c0中space的位置了。  
```python
def listspace(c0, c1):
    spacepos = []
    for idx, chars in enumerate(zip(c0, c1)):
        if (chars[0] ^ chars[1]) in xorSpace:
            spacepos.append(idx)
    return spacepos
```
可以用  
```python
c01 = listspace(c0, c1)
c02 = listspace(c0, c2)
list(set(c01).intersection(c02))
```
輕鬆得到交集結果，也就是 m0 是空白的位置。  

有了space 位置，我們就可以把攻擊對象的字元，一個一個和 space 位置 xor ，再用先前建的字典轉出可能的字串，例如我們隨便轉一組密文的結果：  
```txt
Yolal###,##a ##rb###. #eazest xwrcy#c#n th# worl#.
```
亂碼(我讓它輸出#表示查不到該xor的結果)還不少，但一些字元已足夠我們去猜出明文，例如最後面的the world.；這還只是用只有一組密文的 space 位置當標準，如果我們測試所有密文的 space 位置，開頭字串處理的結果如下：
每行表示目標密文字元和不同密文測試的結果，例如第一行表示第一個字元和另外三個密文測試，兩個沒找到字元，一個轉出Y：   
```txt
"##Y"
"##o"
"d##dl"
"aaa"
"l"
"#e,,##,#"
"ee#"
"#"
"i,,"
"####s###"
"tt #"
"a"
" "
```
已經看得出明文大概是’yodalee is a’，如果再用這明文 `m0 = m1 xor c0 xor c1`，可以試著解其它的明文，找出更多粢訊把亂碼的部分消掉，完成攻擊。  
例如用下面這段簡短的python code，就可以快速測試已知答案的話，其他密文的內容：   
```python
ans0 = "xxx" print("".join([chr(ord(c) ^ c0[i] ^ c1[i]) for i, c in enumerate(ans)])
```
附帶一提，我加密的訊息是：   
```txt
"Yodalee is a garbage. Weakest person in the world."
```
其實不算什麼祕密XD。