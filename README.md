# auto-trade-system-for-Crypto

這個系統使用 tradingview 的 pine Script 判斷下單時間，之後將下單訊號透過 tradingview 的 Webhook Alert 功能傳送至 google cloud run 處理後使用 Binance api 往幣安下單。

部分 tradingview 策略的 Alert 功能有些問題會導致停損的 Alert 無法送出導致大量虧損，所以使用 python 的自動停損程式往幣安發送關單訊號。
