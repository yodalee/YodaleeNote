---
title: "用 Qt Graphics 做一個顯示座標的工具"
date: 2019-12-05
tags:
- Cpp
- Qt
series:
- 用 Qt Graphics 做一個顯示座標的工具 
---

故事是這樣的，平常小弟在公司處理的東西多半是一些 polygon, line 之類的資料，除錯的時候總不能看著 gdb 印出來的 x, y 座標 debug，所以公司同仁有自幹一套 debug 的工具幫忙把這些資料畫出來。
不過呢…這套工具好像在記憶體模型那邊有點問題，資料量大的時候會變超慢；畫圖是直接 call [xlib](https://tronche.com/gui/x/xlib/graphics/drawing/)，每次放大縮小都要重畫所有物件，對記憶體的負擔又更嚴重。只要 polygon 數量突破幾萬個的時候，一次的 refresh 就會花上好幾秒。  
<!--more-->

前陣子手上暫時沒其他緊急的事情，乾脆就用 Qt Graphics 重寫一個，不準在留言問我為什麼不用 nodejs 寫，MaDer 公司的工作站就沒有 nodejs。  
完工後自己試了一陣發現幾十萬個物件的時候放大縮小都超流暢，不愧是 Qt Graphics，雖然程式行數比我預期的多了些，但架構比本來的東西清楚很多。  
其實過程中一直參考強者我同學 AZ 大大的 [QCamber](https://github.com/aitjcize/QCamber)，覺得 AZ大大實在太過**神猛狂強溫**，5-6 年前就寫得出這麼複雜的 project，我一直覺得我寫 code 的時候的整體感很不夠，都是在單一 class 裡面塗塗抹抹，小地方會動可是大架構沒辦法在一開始就訂好，後續要修改的成本就非常高。 Anyway 總之它現有個樣子了，我覺得中間碰過一些實作的問題值得記錄一下，預計可能寫個三篇左右吧。  

----

首先圖形顯示的部分，使用的是 Qt 的 graphics framework，可以用來繪製大量的 2D 物件，支援選取、縮放等等，我們這裡只是要顯示而已，也不用搞得這麼複雜。  
Graphics framework 裡的三個基本元件就是：  

### QGraphicsScene
場景，可以把它想成一塊巨大的畫布，可以在上面自由放上各種 item，Scene 會幫你管理物件的顯示和更新，個人經驗 Scene 負擔到 10 萬個元件左右還很流暢，上到百萬個的時候就會有點頓了（又或者是我把所有 item 都放在 scene 裡面的關係）。
### QGraphicsItem
物件，可以想像成畫素描的時候放的那些石膏，在一個場景上擺上東西，Qt 有提供基本的幾種物件：橢圓 QGraphicsEllipseItem、路徑 QGraphicsPathItem、多邊形 QGraphicsPolygonItem、矩形 QGraphicsRectItem跟文字 QGraphicsSimpleTextItem。
### QGraphicsView
View 是唯一可以在 Qt 的 MainWindow 畫面上出現的物件，可以把 View 想成一台相機，場景 Scene 是不動的，相機從各種角度自由取景，並把取到的景顯示出來，如果取景的尺寸比畫面還要大，跟其他的物件一樣， View 能自動出現捲軸，也可以接收畫面上的滑鼠、鍵盤事件。

只用 Qt 原生的 QGraphicsScene, QGraphicsView, QGraphicsItem 只能組出最基本的顯示工具，變化量非常少，以下就示範一個最基本的設定：  
```cpp
#include <QApplication>
#include <QGraphicsView>
#include <QGraphicsScene>
#include <QGraphicsRectItem>

int main(int argc, char *argv[]) {
  QApplication app(argc, argv);
  QGraphicsScene *scene = new QGraphicsScene;
  scene->setSceneRect(0, 0, 400, 400);
  scene->addItem(new QGraphicsRectItem(50, 50, 150, 100));

  QGraphicsView *view = new QGraphicsView;
  view->setScene(scene);
  view->show();

  return app.exec();
}
```

編譯執行就可以看到這個畫面：   
![simpleqtgraphic](/images/qtpoly/qtpoly_simple.png)

反正這個設計只是一開始建來試驗用的，看一下顯示的效果，很快下一篇就會被我們拆掉了。 