# auto-trade-system-for-Crypto

這個系統使用 tradingview 的 pine Script 判斷下單時間，之後將下單訊號透過 tradingview 的 Webhook Alert 功能傳送至 google cloud run 處理後使用 Binance api 往幣安下單。

部分 tradingview 策略的 Alert 功能有些問題會導致停損的 Alert 無法送出導致大量虧損，所以使用 python 的自動停損程式往幣安發送關單訊號。

## 使用方法

### Tradingview 
1. 建立 tradingview 帳戶，並升級至 Pro 或以上等級來使用 Webhook Alert 功能
2. 選擇想要交易的虛擬貨幣對(交易資料來源必須是幣安)
3. 點選下方的 Pine 編輯器後選擇右方的 開啟 -> 建立新的策略
4. 選擇一個 tradingview pine script，將內容複製進下方輸入區域
5. 點選右方的新增至圖表

### Google Cloud
1. 建立 Google Cloud 帳戶 (每個新帳戶都有三個月 9000 元新台幣的試用餘額可以使用)
2. 點選右上角啟用Cloud shell ，之後點選開啟編輯器
3. 上傳 cloudrun code 內的三個檔案
4. 點選右上角開啟終端機，後在終端機輸入 gcloud run deploy "Project 名稱" --source . --platform managed --region asia-east1 --allow-unauthenticated --port 443
5. 等待建立流程跑完就成功了

## 策略介紹
### SuperTrend tunnal strategy
使用平均K線的 SuperTrend 56 (Multiplier 3) 及 SuperTrend 200 (Multiplier 3) 作為通道使用如果56及200皆出現買進訊號則買進，皆出現賣出訊號則賣出。
這個策略也有止盈功能，當手上有多單時56下穿200則部分止盈，持有賣單則反之。(使用此功能需要勾起設定頁面中的Is TakeProfit)

#### 策略 BackTest 結果:

![image](https://github.com/littleplane321/auto-trade-system-for-Crypto/blob/main/Image/Supertrend%20Tunnal.png)


其餘指標正在研究中  
...coming soon

