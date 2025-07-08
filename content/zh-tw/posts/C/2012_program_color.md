---
title: "程式上色"
date: 2012-09-30
categories:
- c
tags:
- c
series: null
---

其實這是整理在BBS上的舊文，想說就把它轉到這裡來，是記錄如何在程式裡面加上顏色的控制，如果熟BBS的人應該很熟悉，
似乎是一個公訂的標準上色方式，大家參考參考，也許可以讓你的程式增添不少色彩，能不能為人生上色就說不準了。  
<!--more-->

## ANSI C：  
開始上色格式：`\033[x;y;zm`
結束上色格式：`\033[0m`

\033就是escape字元，可以用\e來代替  
x,y,z三數字分別定義字型格式、前景、背景。  

### 格式
| | |
|:-|:-|
| 0 | 無屬性 |
| 1 | 明亮字體 |
| 2 | 暗淡字體 |
| 4 | 底線字體 |
| 7 | 反白字體 |
| 8 | 匿蹤字體 |

### 前景背景
| | 前景| 背景 |
|:-|:-|:-|
| 黑 | 30 | 40 |
| 紅 | 31 | 41 |
| 綠 | 32 | 42 |
| 黃 | 33 | 43 |
| 藍 | 34 | 44 |
| 紫 | 35 | 45 |
| 青 | 36 | 46 |
| 白 | 37 | 47 |

例：
```c
printf("\033[1;33mtest\033[0m")
printf("\e[1;33mtest\e[0m")
```

## BASH shell：  
第一種方法，可以用printf來實作，這和C就是一樣的了。  
至於echo，要用echo -e的方式，讓它解讀escape跳脫 ，之後的寫法也一模一樣。  

值得一提的，這個設定對 [shell prompt](https://wiki.archlinux.org/index.php/Color_Bash_Prompt)也有用，比如說我的PS1參數的設定：
```
PS1="[\e[1;32m\u\e[0m@\e[1;34m\h\e[0m \e[1;33m\W\e[0m]\$"
```
很難看懂，總之，綠色的使用者名稱，藍色的電腦名稱跟黃色的路徑，還滿潮的XD  

## curses.h
雖然說現在用 [curses.h](http://tldp.org/HOWTO/NCURSES-Programming-HOWTO/)
的程式好像滿少了，不過就寫一下吧，主要有五個步驟，那時候在ubuntu上測試是OK。

1. 利用 `has_color()` 偵測是否有顏色支援  
2. `start_color()` 開啟顏色支援  
3. `init_pair(pair,f,b)` 設定屬性  
4. `attrset(COLOR_PAIR(pair))` 設定接下來使用這個屬性來輸出  
5. `attroff(COLOR_PAIR(pair))` 關掉這個屬性  

第三步的 `init_pair` 裡：  
pair指的是要存在第幾個顏色設定暫存中，可以指定`COLOR_PAIRS`組，一般的數值是顏色數量乘顏色數量，但不保證；
在支援高彩度的終端機上面，這個數值可能不會到這麼高，ubuntu10.10終端是64組。  

f 指字體顏色，b 指背景顏色，可以用數字，也可以用 curses.h 中定義好的代碼：  

| code | number |
|:-|:-|
| COLOR_BLACK | 0 |
| COLOR_RED | 1 |
| COLOR_YELLOW | 2 |
| COLOR_GREEN | 3 |
| COLOR_BLUE | 4 |
| COLOR_MAGENTA | 5 |
| COLOR_CYAN | 6 |
| COLOR_WHITE | 7 |

其實順序跟就跟之前提的一模一樣…  

屬性的部分，也有預先定義好的可以使用，
直接 `attrset(A_BOLD)`即可，不同的屬性可以用 | 來加總，不過也別加太多= =。  

| code | effect |
|:-|:-|
| A_NORMAL | 正常 |
| A_STANDOUT | 些許高亮度 |
| A_UNDERLINE | 底線 |
| A_REVERSE | 反白 |
| A_BLINK | 閃鑠 |
| A_DIM | 暗淡 |
| A_BOLD | 粗體 |
| A_PROTECT | 沒試過…不清楚 |
| A_INVIS | 匿蹤 |
| A_ALTCHARSET | 沒試過…不清楚 |
| A_CHARTEXT | 沒試過…不清楚 |

## 結論

顏色上色固然漂亮，可是也會讓輸出的內容變得較難閱讀，請不要太頻繁的使用。