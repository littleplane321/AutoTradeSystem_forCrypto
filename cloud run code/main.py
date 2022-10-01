from flask import Flask,request
from binance.exceptions import BinanceAPIException
from binance import Client


API_KEY = 'Input your Binance API KEY here'
API_Secret = 'Input your Binance API Secret KEY here'

app = Flask(__name__)

@app.route('/Webhook',methods = ['POST'])
def webhook():
    try:
        print("GET POST : ")
        print(request.json)
        webhook_message = request.json
        txn_type = webhook_message['type']
        if(txn_type == 'buy'):
            side = 'BUY'
        else:
            side = 'SELL'
        qty = webhook_message['quantity']
        tag = webhook_message['strategy']
        round_num = webhook_message['round_num']
        reduceonly = webhook_message['reduceOnly']
        if tag == 'test':
            return 'TEST ORDER',200
        
        if tag == 'harmonic_ver2':
            client = Client(api_key=API_KEY, api_secret=API_Secret)
            TP1 = round(float(webhook_message['TP1']),2)
            TP2 = round(float(webhook_message['TP2']),2)
            SL  = round(float(webhook_message['SL']),2)
            """
            try:#平倉功能暫時不用
                client.futures_cancel_all_open_orders(symbol = webhook_message['symbol'])#取消所有掛單
                client.futures_create_order(symbol = webhook_message['symbol'],side = 'SELL' if side == 'BUY' else 'BUY',type = "MARKET",quantity =  float(qty),reduceOnly = 'true')#平倉
            except BinanceAPIException as e:
                print(e)"""
            try:#下單
                client.futures_create_order(symbol = webhook_message['symbol'],side = side ,type = "MARKET",quantity = float(qty),reduceOnly = 'false',newClientOrderId = 'SL:'+str(SL)+'-TP1:'+str(TP1)+'-TP2:'+str(TP2)+'-R:'+str(round_num))#買單
                #client.futures_create_order(symbol = webhook_message['symbol'],side = side ,type = "TAKE_PROFIT_MARKET",price = float(TP1),quantity = float(qty)/2,reduceOnly = 'true')#TP1 price 有問題
                #client.futures_create_order(symbol = webhook_message['symbol'],side = side ,type = "TAKE_PROFIT_MARKET",price = float(TP2),quantity = float(qty)/2,reduceOnly = 'true')#TP2price 有問題
                #client.futures_create_order(symbol = webhook_message['symbol'],side = 'SELL' if side == 'BUY' else 'BUY',price = float(SL),type = "STOP_MARKET",quantity = float(qty),reduceOnly = 'true')#SL price 有問題
            except BinanceAPIException as e:
                print(e)
                return '幣安 ERROR',487
            return 'harmonic_ver2 SUCCESS',200

        if tag == 'Supertrend':
            try:#下單
                client = Client(api_key=API_KEY, api_secret=API_Secret)
                order = client.futures_create_order(symbol = webhook_message['symbol'],side = side,type = "MARKET",quantity = round(qty) if  int(round_num) == 0 else float(round(qty, int(round_num))),reduceOnly = 'false',newOrderRespType = 'RESULT')
            except BinanceAPIException as e:
                print("ERROR!!! : ")
                print(e)
                return '幣安 ERROR',487
            print('下單: ')
            print(order)
            return 'SUCCESS',200
        #test 及 harmonic 以外的訂單
    except Exception as E:
        print("輸入資料錯誤 : " + str(E))
        print("inputdata : ("+str(request.mimetype)+')'+str(request.data))
        return 'Error',487


if __name__ == '__main__':
    app.run(port = 443)