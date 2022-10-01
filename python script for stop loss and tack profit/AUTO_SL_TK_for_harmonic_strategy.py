from binance.um_futures import UMFutures
from binance.websocket.cm_futures.websocket_client import CMFuturesWebsocketClient
from binance.um_futures import UMFutures
from binance.error import ClientError
import websocket
from websocket import _abnf
import time
import json
import _thread


API_KEY = 'Input your Binance API KEY here'
API_Secret = 'Input your Binance API Secret KEY here'

interval = '5m'

Symbols = ['BNBBUSD','BNBUSDT','ETHBUSD','ETHUSDT','BTCUSDT','BTCBUSD']
order_from_bot = []
Thread_Order = None
Thread_Kline = None
Websocket_Kline = None
Websocket_Order = None


Lock =  _thread.allocate_lock()


def On_order_message(ws,message):
    global order_from_bot
    try:
        Msg = json.loads(message)
        if Msg['e'] == "listenKeyExpired":
            ws.close()
            return
        if Msg['e'] != "ORDER_TRADE_UPDATE":
            return
        if Msg['o']['x'] != "NEW":
            return
        if Msg['o']['c'].find('SL') == -1:#ID必須是[SL:XXXX-TP1:XXXX-TP2:XXXX-R:XXXX]
            print("NEW ORDER BUT NOT FROM BOT")
            return

        if Msg['o']['c'] == 'ClosedByBot':
            PairChange = True
            for idx in range(len(order_from_bot)):
                if order_from_bot[idx]["Symbol"] == str(Msg['o']['s']):
                    PairChange = False
            if PairChange:
                Websocket_Kline.close()
                print("Pair Change Restart Websocket")
            return
        
        clientID = Msg['o']['c'].split('-')
        SL = float( clientID[0].split(':')[1] )
        TP1 = float( clientID[1].split(':')[1] )
        TP2 = float( clientID[2].split(':')[1] )
        Roundnumber = int(clientID[3].split(':')[1])
        order = {"Symbol":Msg['o']['s'],"Dircetion":Msg['o']['S'],"SL":SL,"TP1":TP1,"TP2":TP2,"ID":Msg['o']['i'],"Qty":float(Msg['o']['q']),"IsTP1":False,"RoundNumber":Roundnumber}
        print("NEW BOT ORDER" + str(order)+', Local Time :'+str(time.ctime()))
        Lock.acquire()
        NewSymbol = True
        for idx in range(len(order_from_bot)):
            if order_from_bot[idx]["Symbol"] == str(Msg['o']['s']):
                NewSymbol = False
        order_from_bot.append(order)
        Lock.release()
        if NewSymbol:
            if Websocket_Kline != None:
                print("New Pair Restart Websocket")
                Websocket_Kline.close()
            else:
                Thread_Kline = _thread.start_new_thread(Kline_thread,())

            
    except Exception as e:
        print("Order thread error : " + str(e))




def Kline_message(ws,message):
    try:
        Msg = json.loads(message)
        Msg = Msg['data']
        Lock.acquire()
        if Msg['k']['x'] == False:#=========================價格變動就執行
            #print('('+str(Msg['ps'])+') Price : '+str(Msg['k']['c']) +', Kline_Countdown :'+str((float(Msg['k']['T'])-float(Msg['E']))/1000)+'s')
            try:
                for order in order_from_bot:
                    if order["Symbol"] != str(Msg['ps']):
                            continue
                    client =  UMFutures(API_KEY, API_Secret)
                    #TP1
                    if order["IsTP1"] == False:
                        if order["Dircetion"] == "SELL" and (  float(Msg['k']['c']) < order["TP1"] ):
                            Order =  client.new_order(symbol = order["Symbol"],side = 'BUY' ,type = "MARKET",quantity = round( order["Qty"] * 0.6, order["RoundNumber"]),reduceOnly = 'true')#平倉
                            print('('+str(Msg['ps'])+') TP1!!!!  Price : '+str(Msg['k']['c']) +' order INFO : ' + str(order)+', Local Time :'+str(time.ctime()))
                            order["IsTP1"] = True
                        if order["Dircetion"] == "BUY" and (  float(Msg['k']['c']) > order["TP1"] ):
                            Order =  client.new_order(symbol = order["Symbol"],side = 'SELL' ,type = "MARKET",quantity = round( order["Qty"] * 0.6, order["RoundNumber"]),reduceOnly = 'true')#平倉
                            print('('+str(Msg['ps'])+') TP1!!!!  Price : '+str(Msg['k']['c']) +' order INFO : ' + str(order)+', Local Time :'+str(time.ctime()))
                            order["IsTP1"] = True           
                    #TP2
                    if order["IsTP1"] == True:
                        if order["Dircetion"] == "SELL" and (  float(Msg['k']['c']) < order["TP2"] ):
                            Order =  client.new_order(symbol = order["Symbol"],side = 'BUY' ,type = "MARKET",quantity = round( order["Qty"] * 0.4, order["RoundNumber"]),reduceOnly = 'true',newClientOrderId = 'ClosedByBot')#平倉
                            print('('+str(Msg['ps'])+') TP2!!!!  Price : '+str(Msg['k']['c']) +' order INFO : ' + str(order)+', Local Time :'+str(time.ctime()))
                            order_from_bot.remove(order)
                        if order["Dircetion"] == "BUY" and (  float(Msg['k']['c']) > order["TP2"] ):
                            Order =  client.new_order(symbol = order["Symbol"],side = 'SELL' ,type = "MARKET",quantity = round( order["Qty"] * 0.4, order["RoundNumber"]),reduceOnly = 'true',newClientOrderId = 'ClosedByBot')#平倉
                            print('('+str(Msg['ps'])+') TP2!!!!  Price : '+str(Msg['k']['c']) +' order INFO : ' + str(order)+', Local Time :'+str(time.ctime()))
                            order_from_bot.remove(order) 


                    try:
                        #  SL
                        IsStoploss = False
                        if order["Dircetion"] == "SELL" and (  float(Msg['k']['c']) > order["SL"] ):
                            IsStoploss = True
                            Order =  client.new_order(symbol = order["Symbol"],side = 'BUY' ,type = "MARKET",quantity =  order["Qty"],reduceOnly = 'true',newClientOrderId = 'ClosedByBot')#平倉
                            print("Stop Loss !!! : " +str(order)+', Local Time :'+str(time.ctime()))
                            order_from_bot.remove(order)
                            if len(order_from_bot) == 0:
                                ws.close()
                                print("No Order From BOT")
                                Lock.release()
                                return
                        if order["Dircetion"] == "BUY" and (  float(Msg['k']['c']) < order["SL"] ):
                            IsStoploss = True
                            Order =  client.new_order(symbol = order["Symbol"],side = 'SELL' ,type = "MARKET",quantity =  order["Qty"],reduceOnly = 'true',newClientOrderId = 'ClosedByBot')#平倉
                            print("Stop Loss !!! : " +str(order)+', Local Time :'+str(time.ctime()))
                            order_from_bot.remove(order)
                            if len(order_from_bot) == 0:
                                ws.close()
                                print("No Order From BOT")
                                Lock.release()
                                return

                    except ClientError as e:
                        print(e)
                        pass
                Lock.release()
            except Exception as e:
                print("Error AT TP!! : " + str(e))
            return
        #======================================收盤後執行
        print('('+str(Msg['ps'])+') Price : '+str(Msg['k']['c']) +', Local Time :'+str(time.ctime()))
        if len(order_from_bot) == 0:
            ws.close()
            print("No Order From BOT")
            Lock.release()
            return
            '''
        client =  UMFutures(API_KEY, API_Secret)
        for order in order_from_bot:
            try:
                if order["Symbol"] != str(Msg['ps']):
                    continue
                #  SL
                IsStoploss = False
                if order["Dircetion"] == "SELL" and (  float(Msg['k']['c']) > order["SL"] ):
                    IsStoploss = True
                    Order =  client.new_order(symbol = order["Symbol"],side = 'BUY' ,type = "MARKET",quantity =  order["Qty"],reduceOnly = 'true',newClientOrderId = 'ClosedByBot')#平倉
                    print("Stop Loss !!! : " +str(order)+', Local Time :'+str(time.ctime()))
                    order_from_bot.remove(order)
                    if len(order_from_bot) == 0:
                        ws.close()
                        print("No Order From BOT")
                        Lock.release()
                        return
                if order["Dircetion"] == "BUY" and (  float(Msg['k']['c']) < order["SL"] ):
                    IsStoploss = True
                    Order =  client.new_order(symbol = order["Symbol"],side = 'SELL' ,type = "MARKET",quantity =  order["Qty"],reduceOnly = 'true',newClientOrderId = 'ClosedByBot')#平倉
                    print("Stop Loss !!! : " +str(order)+', Local Time :'+str(time.ctime()))
                    order_from_bot.remove(order)
                    if len(order_from_bot) == 0:
                        ws.close()
                        print("No Order From BOT")
                        Lock.release()
                        return

            except ClientError as e:
                print(e)
                pass'''

        Lock.release()
    except Exception as e:
        print('Kline Thread Error!!')
        print(e)
        

def on_error(ws, error):
    print("Websock ERROR!! : " + str(ws.url))
    print(error.args)
    if(error.args[0] == 10054):
        print("斷線 "+', Local Time :'+str(time.ctime()))
        print('重試連線')

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws):
    print("Opened connection : "+str(ws.url))


def Kline_thread(*args):
    global Websocket_Kline
    while True:
        Lock.acquire()
        if len(order_from_bot) >0 :
            Lock.release()
            Baseurl_forKline = 'wss://fstream.binance.com/stream?streams='
            Temp_Symbollist = []
            for idx in range(len(order_from_bot)):
                if Temp_Symbollist.count(order_from_bot[idx]["Symbol"]) == 0 :
                    Temp_Symbollist.append(order_from_bot[idx]["Symbol"])
                    Baseurl_forKline += order_from_bot[idx]["Symbol"].lower() + '_perpetual@continuousKline_' + interval + '/'       
            Baseurl_forKline = Baseurl_forKline.strip('/')
            print(Baseurl_forKline)
            Websocket_Kline = websocket.WebSocketApp(Baseurl_forKline,
                                    on_open=on_open,
                                    on_message=Kline_message,
                                    on_error=on_error,
                                    on_close=on_close
                                    )
            Websocket_Kline.run_forever()
            print("k-Line websocket closed")
        if Lock.locked():
            Lock.release()
        time.sleep(1)

def OrderMsg_thread(*args):
    global Websocket_Order
    while True:
        try:
            client = UMFutures(API_KEY)
            ListenKey = client.new_listen_key()['listenKey']
            Baseurl_fortradedata = 'wss://fstream.binance.com/ws/'+ListenKey
            Websocket_Order = websocket.WebSocketApp(Baseurl_fortradedata,
                                    on_open=on_open,
                                    on_message=On_order_message,
                                    on_error=on_error,
                                    on_close=on_close
                                    )
            Websocket_Order.run_forever()
            print("Msg thread Out : Try To Reconnect")
        except Exception as e:
            print("Order Thread Error : " + e)
    
    


def main():
    websocket.enableTrace(False)
    client = UMFutures(API_KEY)
    response = client.new_listen_key()

    '''orders = client.get_all_orders(symbol='BNBBUSD',limit = 30)
    orders = json.loads(orders)
    for order in orders:
        if order["status"] != "New":
            continue
        if  order["clientOrderId"].find('SL') == -1:
            continue
        clientID = order["clientOrderId"].split('-')
        SL = float( clientID[0].split(':')[1] )
        TP1 = float( clientID[1].split(':')[1] )
        TP2 = float( clientID[2].split(':')[1] )
        Roundnumber = int(clientID[3].split(':')[1])
        neworder = {"Symbol":order["symbol"],"Dircetion":order["side"],"SL":SL,"TP1":TP1,"TP2":TP2,"ID":order["orderId"],"Qty":float(order["origQty"]),"IsTP1":False,"RoundNumber":Roundnumber}
        order_from_bot.append(neworder)'''
    print("Auto Stop Loss Bot Start!!")
    Thread_Order = _thread.start_new_thread(OrderMsg_thread,())
    #Thread_Kline = _thread.start_new_thread(Kline_thread,())



    while True:
        time.sleep(600)
        print('renew_listen_key'+', Local Time :'+str(time.ctime()))
        client.renew_listen_key(response['listenKey'])
        Websocket_Order.send('',opcode=_abnf.ABNF.OPCODE_PONG)
    



if __name__ == "__main__":
   main()