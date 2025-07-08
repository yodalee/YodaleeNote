---
title: "自幹世界線變動率探測儀（Nixie Tube Clock）：寫 code"
date: 2018-10-27
categories:
- hardware
tags:
- hardware
- NixieClock
series:
- 自幹世界線變動率探測儀(Nixie Tube Clock)
forkme: nixieclock
---

到了這邊木已成舟（無誤，電路板沒做好的話，程式寫再多都沒有用www，只能硬著頭皮去修或者認命掏銀子出來重洗了），再來就是不斷的寫 code 跟燒 code。
<!--more-->
在洗板的時候已經預留了燒錄程式碼的接點，只要把對應的針腳從作為燒錄器的 Arduino 板子接到電路板上就能燒錄了。  
寫Code的時候要注意，如果一不小心把所有的燈管都打開，高壓電路有可能會推不動，淘寶上買的高壓電路板是推得動，我的不行，我猜跟電感的好壞有關；這版電路因為有用上 74HC238跟 74CD4514，原則上來說是不會發生這種事。  

建議可以先從低壓的部分先測試，因為我們在 78M05 輸出到所有需要 5V 的電路上有斷路器，這樣就可以先斷路，用外接的 5V 驅動整個電路了。  
測試 LED，把 LED 腳位輪流打開就行了：  
{{< youtube duBaHfir7NA >}}

靠北，超級炫砲……  
LED 5050 RGB，我藍、紅是用 270 歐姆，綠色用 620 歐姆，結果他爸還是超級亮…我個人是覺得有點太亮，測程式的時候都快被閃瞎了，有點妨害看燈管，如果可以的話應該要再換大一點的電阻，把光度調小一點。  
Github 裡面有附上 74HC238 跟 74CD4514 的測試程式，可以執行後一個一個量測兩個晶片的輸出，看看有沒有正常動作。  

軟體中燈管要顯示的數字存在 Byte 裡面，0-9 對應 0-9，左點跟右點分別是 10 跟 11，照著 Byte 的位元寫給 74CD4514，12-15 則是會把 74CD4514 的 INH 降下來把燈管關掉。  
```c
void writeNum(byte num) {
  if (num >= 12) {
    digitalWrite(DISPLAY_E, HIGH);
  } else {
    byte mappedNum = mapNum(num);
    digitalWrite(DISPLAY_E, LOW);
    digitalWrite(DISPLAY_3, (mappedNum >> 3) & 0x1);
    digitalWrite(DISPLAY_2, (mappedNum >> 2) & 0x1);
    digitalWrite(DISPLAY_1, (mappedNum >> 1) & 0x1);
    digitalWrite(DISPLAY_0, (mappedNum >> 0) & 0x1);
  }
}
```
這裡要特別注意一下，**如果要取出數字裡某個 bit 的時候，要用的運算符號是 & bitwise and ，不是 ^ bitwise xor 噢 ^.<**   
為什麼會有那個 mapNum ，其實是我 v1.01 的 layout …畫錯了，不確定是不是用的 footprint 的問題還是我自己蠢，總之陰極控制的接線是錯的，從 1-9 的接線完全反過來了。
幸好這個 bug 可以用軟體修正回來，寫一個函式去轉數字就好了，這個也是 v1.02 修正。我覺得機率最高的原因，是我在看[參考資料](http://www.tube-tester.com/sites/nixie/data/in-14/in-14.htm)的圖的時候，沒有注意到它是 Bottom view，在設定 schematic to layout 的時候寫反了，最後 layout 也就錯了。  
燈管的選擇 writeTube 和這裡一樣，0-7 各 bit 送給 74HC238 的三個腳位，就能開關某一支燈管，很簡單可以打包成一個函式來選擇燈管，首先我們就先寫一個掃描的程式，用 for loop確認每個燈管每隻腳位都有正常運作。   
{{< youtube yUsdp3tUh6w >}}
正常。  
有了這兩個小函式，可以把燈管的值保存在全域變數陣列 display，然後用一個函式來更新它，只要這個函式在 loop() 中，燈管就會不斷顯示 display 的值；delay 只能是 delay(1) 或 delay(2) ，算是實驗得到的經驗值，不放 delay 的話切換速度太快，所有管子的數字會混在一起，delay(3) 的話則是看得出有點在閃。  
```c
void updateTube() {
  for (int tube = 0; tube < NTUBE; tube++) {
    writeTube(tube);
    writeNum(display[tube]);
    delay(2);
  }
}
```
## 使用 DS1307 記錄時間

知道如何顯示數字之後，再來就是去接 RTC 時間，這裡我是使用別人[包好的 DS1307RTC](http://playground.arduino.cc/Code/Time)，照著範例把 library 引入之後，在 setup 呼叫 setSyncProvider(RTC.get);  
即可和 DS1307 同步，之後就可以很方便的用 year(), month() 等函式拿到現在的時間值，非常方便。  

### DS1307 Interrupt

DS1307 的 SQW 腳位能設定穩定輸出方波，搭配 arduino interrupt 就能每秒呼叫函式做點事情，我們已經把 DS1307 的 SQW 腳位接給 ATmega328p 的 digital pin 2，只要透過 Wire 向 ds1307 設定（請參考 ds1307 datasheet），其中 DS1307\_ADDR 是 DS1307 的 I2C 位址 0x68，再對偏移 0x7 的位址寫入設定 0x10 即可，DS1307 可以設定輸出 1kHz, 4.096 kHz, 8.192 kHz 和 32.768 kHz 的方波：  
```c
Wire.begin();
Wire.beginTransmission(DS1307_ADDR);
Wire.write(0x07);
Wire.write(0x10);  // Set Square Wave to 1 Hz
Wire.endTransmission();
```
設定完 ds1307 就會輸出頻率 1Hz 的方波，我們可以把這個方波接給 ISR 來做計算開機秒數的工作：  
```c
void ISR_RTC() {
  toggle = !toggle;
  ++secCount;
}
attachInterrupt(digitalPinToInterrupt(RTC_SQW), ISR_RTC, RISING);
```
後來發現算秒數好像不能幹嘛XDDD  

## 使用 DS1307 NV RAM 記錄資訊

為了記錄世界線的資料，我們要用 DS1307 上面 56 bytes 的 NVRam 記錄資訊，不知道為什麼 DS1307 library 都不支援這功能，參考 [arduino 論壇](http://forum.arduino.cc/index.php?topic=152248.0)包了兩個函式來讀寫 NVRam，RAM\_OFFSET 是 0x8，這樣就能把世界線的資料記錄在 NVRam 裡面了。  
```c
 void writeNVRam(byte offset, byte *buf, byte nBytes) {
  Wire.beginTransmission(DS1307_ADDR);
  Wire.write(RAM_OFFSET + offset);
  for (int i = 0; i < nBytes; i++) {
    Wire.write(buf[i]);
  }
  Wire.endTransmission();
}

void readNVRam(byte offset, byte *buf, byte nBytes) {
  Wire.beginTransmission(DS1307_ADDR);
  Wire.write(RAM_OFFSET + offset);
  Wire.endTransmission();
  Wire.requestFrom( (uint8_t)DS1307_ADDR, nBytes);
  for (byte i = 0; i < nBytes; i++) {
    buf[i] = Wire.read();
  }
}
```
剩下的好像就是把上面的 code 猛攪一陣，就可以做出各種不同功能了。  

要讀取按鈕的動態，可以參考官方文件 [Debounce](https://www.arduino.cc/en/Tutorial/Debounce)  
整個 loop 裡面的流程，大概就是保存一個 state 的變數，然後依序  
1. 檢查 button 1 有沒有按下，有的話做一點事
2. 檢查 button 2 有沒有按下，有的話做一點事
3. 依不同的 state ，設定 LED 跟輝光管顯示值的 display 陣列
4. 呼叫 updateLED() 跟 updateTube() 顯示資訊。  

我是設計有五個模式：
1. 自動切換
2. 時間HH.MM.SS
3. 日期YYYYMMDD
4. 世界線顯示
5. 全關省電模式

詳情請參考 [github repository](https://github.com/yodalee/NixieClock)，這樣把自己寫的爛 code 展現在大家眼前感覺真是羞恥。  

整體 code 差不多就是這樣啦，硬體能動之後改軟體什麼的都不算太難了，想玩的話可以弄一些，像是發送第一封 D-Mail： 

{{< youtube egiKm6L4Y-A >}}
