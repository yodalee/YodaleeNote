---
title: "scanf整理"
date: 2012-01-14
categories:
- c
tags:
- c
series: null
---

最近寫了很多檔案處理的程式，涉及許多字串中，包含數字符號、跳行的內容，不斷的看許多scanf的相關文件，把它整理在這裡，供大家參考。  
<!--more-->

scanf簡單來說就是格式化輸入，使用上長這樣：  
```c
int scanf(format, argument pointer list)
int fscanf(FILE* , format, argument pointer list)
int sscanf(char *, format, argument pointer list)
```

這裡集中在format要怎麼寫：  

## 基本規則：   
* 空白字元：tab、\n，match 到任意字元的空白、tab、\n、或都都不 match
* 一般字元：一定要全部match

基本規則就這麼簡單
## % 的規則：  
% 後為特殊字元，需要在argument pointer list中有相對應的pointer，語法為：

```txt
% * n modifier type
```

### type 整理如下：

| type character | input | argument |
|:-|:-|:-|
|%| 一個 % 字元 ||
|d| signed decimal | int * |
|i| signed/unsigned decimal | int * |
|oux| 8/10/16 進位讀入 unsigned int | int * |
|fegE| float | float * |
| s | 輸入字串直到空白 | char *|
| c | 輸入字元 | char * |
| p | 輸入 pointer | void ** |
| n | 不 mathc，直接填入目前為止 match 的字串 | int * |
| [] | match [] 中任意字元 | char * |

補充說明幾點：
* d 跟 i 的差別在於，i 可以接受各種進位的輸入
以 0x 為首則以16進位讀入，以0為首則以8進位讀入。  
```c
scanf("%i",&a)
0x10
a = 16
```

* 用 s 輸入字串，一定要注意 char* 有 malloc 足夠空間
* n 會回傳到目前為止讀入的字元數
```c
int n, a;
scanf("%d%n", &a, &n);
> 123
> n = 3
```

* [] 的用法  
%[a-z] 表示match到a-z中任意字元  
%[^aeiou1-9] 表示match到並非aeiou和1－9字元  

### *n 規則：
* *決定這筆資料是否要存入argument 中
* n 決定要讀入多少個char     
```c
int a;
scanf("%d"); //runtime error, 讀入東西沒地方存，seg fault
scanf("%d", a); //runtime error, 是&a，這很容易忘記
scanf("%d", ＆a);  // 正確用法
scanf("%*d"); //OK，讀入的數字就dump掉
scanf("%3d",＆a); //輸入4444，a＝444
```

搭配上面的[]，scanf就變得超強大，比如說常有人問要如何換行？  
其實只要這樣就是換一行。  
```c
scanf("%*[^\n]\n")
```

### modifier  
modifier 決定讀入的資料要如何儲存，以下是modifier的選項，不過除了lL以外，好像也不常用（？）：

| modifier | 存入型別 |
|:-|:-|
|h | short int |
|hh | char |
| j | (C99) intN_t |
| I | efg double, diouxX long |
| L | efg long double, diouxX long long |
| t | (C99) ptrdiff_t |
| z | (C99) size_t |