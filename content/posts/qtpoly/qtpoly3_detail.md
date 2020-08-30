---
title: "用 Qt Graphics 做一個顯示座標的工具 - 細節調整"
date: 2019-12-14
tags:
- Cpp
- Qt
series:
- 用 Qt Graphics 做一個顯示座標的工具 
---

其實這篇才是我寫文的主因，前面兩篇其實都是前言（欸），總之就是我埋頭自幹 AZ 大大吃一頓飯就寫得出來的工具，結果過程中寫得亂七八糟，有時候該出現的東西就是不出現測到頭很痛，或是測一測就進無窮迴圈後來發現是自己蠢，發了 v0.1 之後被靠北顯示怎麼這麼醜，想改又很難搜不到解法QQ。  
當然最後還是搜到了，但就希望可以多寫一篇文，讓這些解法更容易被搜到，如果運氣很好真的幫到人也算功德一件，~~如果你真的被幫到的話，麻煩幫我這篇文章留下一個 like 然後順手按下旁邊的訂閱和小鈴鐺~~（醒醒這裡是 blogger 不是 youtube。  
<!--more-->

## 畫上座標線：

這算是一個附加功能，一般的顯示工具只要設定 Scene 的 [background brush](https://doc.qt.io/qt-5/qgraphicsscene.html#backgroundBrush-prop)，設定一個黑色的 brush，就能畫出黑色背景了。  
但如果我們要更精細的話，就要去實作 scene 或是 view 的 [drawBackground](https://doc.qt.io/qt-5/qgraphicsscene.html#drawBackground) 函式：  
```cpp
void drawBackground(QPainter *painter, const QRectF &rect)    
```
下面是我實作的程式碼節錄，有幾個可以注意的地方：  

1. Qt 的座標系統左上角是 0,0，往右往下是 x 遞增跟 y 遞增，所以用 top 的值會比 bottom 小。
2. 這個函式參數是一個 QPainter 跟一個 QRectF，painter 好理解就是目前作畫的對象，在這個 painter 上面作畫就會畫在背景上；QRectF 一般會認為就是現在顯示背景的矩形，不過不對，它是「現在要更新背景的範圍的矩形」。  
例如我現在顯示的 Scene 大小是 -50,-50 ~ 50, 50，但我實作滑鼠可以在 scene 上面拉一個選取的小框框，在我拉框框的時候，Qt 會判定只有這個小框框裡面的背景是需要重畫的，QRectF 就會設定到這個小框框上；其實某種程度來看這樣也對，而且更節省重畫的資源。
3. 承上點，所以有抓到現在 scene 的大小要怎麼辦？這也是我為什麼選擇是實作 View 的 drawBackground 而不是 Scene 的，因為我可以透過 `mapToScene(viewport()->rect()).boundingRect() `取得這個 View 現在顯示 Scene 的大小。

後來就是一些數學計算，在對應的座標點上呼叫 drawPoint 了，下面的 code 我有略為刪節過了，要用的話不要全抄。  
```cpp
void
MyViewer::drawBackground(QPainter *painter, const QRectF &rect) {
  qreal left         = rect.left();
  qreal right      = rect.right();
  qreal top         = rect.top();
  qreal bottom = rect.bottom();

  QRectF sceneRect = mapToScene(viewport()->rect()).boundingRect();
  qreal size = qMax(sceneRect.width(), sceneRect.height());
  qreal step = qPow(10, qFloor(log10(size/4)));

  qreal snap_l = qFloor(left / step) * step;
  qreal snap_r = qFloor(right / step) * step;
  qreal snap_b = qFloor(bottom / step) * step;
  qreal snap_t = qFloor(top / step) * step; 

  // print coordinate point
  for (qreal x = snap_l; x <= snap_r; x += step) {
    for (qreal y = snap_t; y <= snap_b; y += step) {
      painter->drawPoint(x, y);
    }
  }

  // print coordinate line
  painter->drawLine(qFloor(left), 0, qCeil(right), 0);
  painter->drawLine(0, qCeil(bottom), 0, qFloor(top));
  QGraphicsView::drawBackground(painter, rect);
}
```

## 不動物件：
第一個是所謂的不動物件，也就是 QGraphicsItem 透過設定了 [ItemIgnoresTransformations flag](https://doc.qt.io/archives/qt-4.8/qgraphicsitem.html#GraphicsItemFlag-enum)，這樣這個 item 就不會受到 view 視角變化的影響。  

使用情境也很單純，像是在畫面上打個 marker 或是寫上文字，如果視窗縮小就看不到就奇怪了，所以這個 marker 就要設定這個 flag，放大縮小都會顯示一樣。  
改變就是呼叫：
```cpp
setFlag(QGraphicsItem::ItemIgnoresTransformations, true);  就可以了。  
```

要注意的是在設定了這個 flag 之後，在這個 item 裡面的位移似乎會失去效果（還是行為會變很怪，我有點忘了），一般要在一個位置例如 100, 100 畫一個正方形，我們可以用 QGraphicsRectItem，在 100, 100 的地方畫正方形；如果是 ignore transformation 的物件，我是變成在 0,0 的位置畫一個正方形，然後把物件的位置用 setPos 設定在 100, 100。  
這部分當初真的弄超久，後來覺得這樣不行，把放在 dropbox 裡面的 <c++ GUI Programming With Qt 4> 拿出來翻翻，沒想到在第八章 Qt graphics 章節就講了要怎麼寫類似的東西，還有範例 code ，果然寫程式還是要多看書而不是瞎攪和，弄了好一陣子的東西其實書上的範例都寫了。  

## 填充物：

上一篇文的最後一張圖，應該很明顯可以看到，我用 brush 填進去的東西，非常的…不均勻，一格一格的非常醜，實際運作的 code 也是，只要放大縮小填充物的就會變得不連續。  
這是因為 QBrush 在填東西的時候，用固定密度在填充，不會隨著螢幕的放大縮小改變填充物的密度，要修成也只需要一行，在 paint 函式裡面加上這個：  
```cpp
QBrush m_brush;
m_brush.setTransform(QTransform(painter->worldTransform().inverted()));
painter->setBrush(m_brush)
```
把現在場景的變形反轉補償回去就可以了；這個解答出自 [Stack Overflow](https://stackoverflow.com/questions/13958385/how-to-make-qt-qgraphicsview-scale-to-not-affect-stipple-pattern)。  

## 隨放大縮小調整長度：

同樣的是另一張圖的箭頭，在放大縮小的時候，箭頭的部分會跟著放大縮小，這是我們不想要的，因為縮太小的時候箭頭會看不到，這時候就要用到我們上篇提到的 QStyleOptionGraphicsItem，在 paint 函式裡面，可以用這個東西從 painter 的 transform 裡取得 level of detail (LOD)：  
```cpp
qreal qScale = option->levelOfDetailFromTransform(painter->worldTransform());
qreal len = 10 / qScale;
```
qScale 就是目前放大值，可以用它調整我們要畫的長度 len；這個解答出自 [Heresy's Space](https://kheresy.wordpress.com/2011/10/07/%E5%BB%BA%E7%AB%8B%E4%B8%80%E5%80%8B%E4%B8%8D%E8%A2%AB-view-%E5%BD%B1%E9%9F%BF%E7%B7%9A%E6%A2%9D%E5%AF%AC%E5%BA%A6-graphics-item/)。  

## 參考書目
* C++ GUI Programming With Qt 4
* Game Programming using Qt 5 Beginner's Guide: Create amazing games with Qt 5, C++, and Qt Quick


