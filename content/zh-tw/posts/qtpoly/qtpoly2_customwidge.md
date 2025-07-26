---
title: "用 Qt Graphics 做一個顯示座標的工具 - 客製化元件"
date: 2019-12-11
tags:
- Cpp
- Qt
series:
- 用 Qt Graphics 做一個顯示座標的工具 
---

上一篇我們介紹了 Scene, View, Item 的關係，這篇就來客製化一下，畢竟 Qt 的元件沒客製化功能都非常受限，預設行為幾乎什麼都沒有，這時候就是好好重溫 C++ 最美妙功能––繼承的時候了。  
<!--more-->
首先是 Scene 跟 View，都用繼承的方式建一個自己的 class，才能在裡面實作各種信號跟插槽，設計上 Scene 是 View 的 data member，View 上面接到什麼東西直接 pass 給 Scene，實作就不一一介紹，下面是一個簡單的修改列表，因為是內部用的工具就沒辦法把程式碼貼上來給大家笑了：  

### View實作事件：  
* keyPressEvent：客製化按鍵盤的行為。
* wheelEvent：連接到放大縮小的函式。

### View實作插槽：  
* clearScene：清空畫面
* addItem：接收讀進來的物件，往下直接呼叫 Scene 的 addItem。
* zoomToAll 跟 zoomRect：放大縮小。

### Scene 實作事件：  
* mousePressEvent/mouseMoveEvent/mouseReleaseEvent：定義滑鼠行為。

### Scene 實作信號：  
* rectSelected：滑鼠事件會發出這個信號，通知 View 跟 MainWindow。
* mouseClick：同樣用來通知 MainWindow 使用者點在哪裡。

當然我們也要客製化自己的 [QGraphicsItem](https://doc.qt.io/archives/qt-4.8/qgraphicsrectitem.html)，當然如果要顯示的東西沒太多特別要求，只靠 Qt 提供的那些 QGraphicsXXXItem 也是 OK 的。  
我記得在實作時候也有考慮過是不是繼承 [QAbstractGraphicsShapeItem](https://doc.qt.io/archives/qt-4.8/qabstractgraphicsshapeitem.html) 就好，後來好像因為什麼原因，還是繼承 QGraphicsItem。  

照著 Qt 的[說明文件](https://doc.qt.io/qt-5/qgraphicsitem.html#details)，要實作自己的 QGraphicsItem，重點在打造兩個函式：  
```cpp
QRectF boundingRect() const override
```
這個函式要回傳一個 QRectF，標示這個 Item 的大概位置，讓 Scene 能用它作分類跟檢索，如果設錯的話就有可能變成 item 明明在某個位置視窗卻打死不顯示它，因為 Scene 在檢索的時候就不認為這個 Item 有需要顯示。  
```cpp
void paint(
  QPainter *painter,
  const QStyleOptionGraphicsItem *option,
  QWidget *widget) override
```
Paint 就是操作 Painter 裡面的函式盡情的作畫，不過我自己是省得麻煩，都是創一個 QPainterPath 然後呼叫 [Painter](https://doc.qt.io/qt-5/qpainter.html) 的 drawPath，這樣比較簡單。  
舉例來說我自己實作的一個物件是在視窗上面標上一個箭頭然後顯示文字，大略來說程式碼就是這樣：  
```cpp
QPainterPath path;
path.moveTo(0, 0);
path.lineTo(0, 8);
path.lineTo(5.656, 5.656);
path.closeSubpath();
path.lineTo(7.65, 18.48); // len 20, tilt 22.5
path.setFillRule(Qt::WindingFill);
QFont serif("Helvetica", 12);
path.addText(QPoint(0, 0), serif, m_text);
```
paint 裡再用 drawPath 把這條 path 畫出來就可以了。  

Paint 的另外兩個參數 QStyleOptionGraphicsItem 和 QWidget，前者帶著顯示上要用的參數，在下篇做一些細部設定的時候會用到；後者則指向目前繪圖中的物件，通常可以不用管它，我也還不確定什麼時候會用到它。  
這次實作全面採用 C++ 的新關鍵字 override，個人認為真的好用，像是上面的 boundingRect 如果沒寫 const 的話其實是在實作不同的函式，加了 override 編譯器就會跳錯誤，比較不會犯這種不容易注意到的錯。  

實作 QGraphicsItem 以我們的應用這樣就夠了，如果還需要更精細的管理，可以再實作函式：  
```cpp
QPainterPath shape() const
```
這個函式用來檢查碰撞、滑鼠有沒有點在物件上等等，不實作預設就是以 boundingRect 代替。  

自己幹完 QGraphicsItem 之後，整個程式也有了個樣子了，繼承自 QGraphicsItem 的物件可以直接用 addItem 塞進 Scene 裡面，下面截兩張運作起來的樣子，分別是顯示箭頭跟一個三角形的多邊形：  
![arrow](/images/qtpoly/arrow.png)
![polygon](/images/qtpoly/polygon.png)

還有很多細部設定沒做所以看起來會有一點粗糙，下一篇預定就是要講這些細部的東西。 