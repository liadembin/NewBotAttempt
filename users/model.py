
import requests
import schedule
import os 
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
from tensorflow.keras.models import load_model
import tensorflow.keras.backend as K
import math
import datetime
import yfinance as yf
import pandas as pd
import numpy as np



class Model:
    def __init__(self, modelPath, token, maxPath, idd="/KerasModels/Model1", buyTimes=["16:35", "20:00"], secondsWaitingForStopLoss=45):
        def smape_loss(y_true, y_pred):
            epsilon = 0.1
            summ = K.maximum(K.abs(y_true) + K.abs(y_pred) +
                             epsilon, 0.5 + epsilon)
            smape = K.abs(y_pred - y_true) / summ * 2.0
            return smape * 100.0
        self.model = load_model(modelPath, custom_objects={
            "smape_loss": smape_loss
        })
        self.idd = idd
        self.ticker = "tqqq"
        self._token = token
        self.buyTimes = buyTimes
        self.number_of_stocks = 10
        self.serverBaseUrl = "http://localhost:8000/"
        self.stopLossRunningTime = 0
        self.maxPath = maxPath
        self.secondsWaitingForStopLoss = secondsWaitingForStopLoss
        self.DecideBuyOrSell()
        self.scedule()
    def buy(self, fromStop=False):
        n = (self.GetStockAmount())
        if fromStop:
            n = abs(self.GetStockAmount())
            print('from stop')
            print(n)
        try:
            self.request("http://localhost:8000/buy",  number=n)
        except Exception as e:
            print("buyerr")
            print(e)

    def sell(self, fromStop=False):
        try:
            self.request("http://localhost:8000/sell",
                         number=self.GetStockAmount())
        except Exception as e:
            print("sell err")
            print(e)

    def short(self):
        try:

            url = "http://localhost:8000/short"

            payload = {
                "token": self._token,
                "number_of_stocks": abs(self.computeStockNumber()),
                "ticker": self.ticker
            }
            headers = {"Content-Type": "application/json"}

            response = requests.request(
                "POST", url, json=payload, headers=headers)

            print(response.text)
            print("shorting")
            now = datetime.datetime.now()
            with open(f"./{self.idd}/logs.txt", "a") as f:
                f.write(
                    f'request to {url} with payload {payload} at time {now.strftime("%d/%m/%Y %H:%M:%S")}')
        except Exception as e:
            print("short err ")
            print(e)

    def GetStockAmount(self):
        url = "http://localhost:8000/getMyStockNumber"

        headers = {"Authorization": "Bearear eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6NiwidXNlcm5hbWUiOiJwbHBsIiwiaWF0IjoxNjYwMDI4MTE5fQ.SABgFBI6E1XAYrLiIg76vwaf5nk445sJeyGXwQ_FiT0"}

        response = requests.request("GET", url, headers=headers)

        print(response.text)
        return response.json()['numberofstocks']

    def request(self, url, number=False):
        print("token : ", self._token)
        print("ticker:", self.ticker)
        print("num :", number or self.computeStockNumber())

        payload = {
            "token": self._token,
            "number_of_stocks": self.computeStockNumber(),
            "ticker": self.ticker
        }
        if number != False:
            # payload['number_of_stocks'] = number
            payload.update({
                'number_of_stocks': number
            })

        print("payload")
        headers = {"Content-Type": "application/json"}
        print("req")
        response = requests.request("POST", url, json=payload, headers=headers)
        print("res text:")
        print(response.text)
        print("res json: ")
        print(response.json())
        now = datetime.datetime.now()
        with open(f"./{self.idd}/logs.txt", "a") as f:
            f.write(
                f'request to {url} with payload {payload} at time {now.strftime("%d/%m/%Y %H:%M:%S")}')
        return response.json()

    def computeStockNumber(self):
        
        data = yf.download("tqqq", interval='1m', period='1d')
        return math.floor((self.getMyBalance() * .2) // data['Adj Close'][-1])

    def getDoIown(self):
        url = "http://localhost:8000/myPortfolio"
        payload = {"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6NiwidXNlcm5hbWUiOiJwbHBsIiwiaWF0IjoxNjYwMDI4MTE5fQ.SABgFBI6E1XAYrLiIg76vwaf5nk445sJeyGXwQ_FiT0"}
        response = requests.request("POST", url, json=payload)
        jso = response.json()
        results = jso['result']
        Owns = False
        isShort = False
        for purchase in results:
            if purchase['ticker'] == self.ticker and purchase['numberofstocks'] != 0:
                isShort = purchase['numberofstocks'] < 0
                Owns = True
                break
        print(response.text)
        return (Owns, isShort)

    def isInPosition(self):
        pass

    def DecideBuyOrSell(self):

        if self.getDoIown()[0]:
            return print("position already active")
        prediction = self.predict()

        todayPrice = yf.download("tqqq", interval='1m', period='1d')
        price = todayPrice['Adj Close'][-1]
        bought = False
        if prediction > price:
            self.buy()
            bought = True
        elif prediction < price:
            self.short()
            bought = True
        if bought:
            with open(f"./{self.idd}/BP.txt", "w") as f:
                f.write(str(price))
            with open(f"./{self.idd}/PP.txt", "w") as f:
                f.write(str(prediction))

    def getMyBalance(self):
        url = "http://localhost:8000/getMyBalance"
        headers = {"Authorization": "Bearear " + self._token}
        response = requests.request("GET", url, headers=headers)
        print(response.text)
        return response.json()['currentCash']

    def predict(self):
        X = self.generateData()
        return (self.model.predict(X)[-1] * pd.read_csv(self.maxPath)['max'][0])[0]

    def generateData(self):
        data = yf.download(self.ticker, period='730d', interval='1h')
        maxe = pd.read_csv(self.maxPath)
        # data /= maxe['']
        for i, col in enumerate(maxe.col, 0):
            print(i, col)
            data[col] /= maxe['max'][i]
        print(data.head(3))
        X = []
        y = []
        window_size = 60
        data_arr = data.to_numpy("float64")
        for i in range(0, len(data_arr)-window_size):
            X.append(data_arr[i:i+window_size])
            y.append(data_arr[i+window_size, 0])
        X = np.array(X)
        y = np.array(y)
        print("X shape: ", X.shape)
        print("y shape: ", y.shape)
        return X[int(len(X) * 0.95)].reshape([-1, 60, 6])

    def DecideStopLoss(self):
        (own, isShort) = self.getDoIown()
        if not own:
            return print("no active position")
        # return
        todayPrice = yf.download("tqqq", interval='1m', period='1d')[
            'Adj Close'][-1]
        with open(f"./{self.idd}/BP.txt", "r+") as f:
            BuyPrice = float(f.read())
        with open(f"./{self.idd}/PP.txt", "r+") as f:
            PredictedPrice = float(f.read())

        # upper is 60% of seen diffrence in price
        # todayPrice >= 0.6 * (BuyPrice - PredictedPrice)
        # if long >= elif short <=
        if not isShort:
            if todayPrice >= 0.6 * (BuyPrice - PredictedPrice):
                print("stop loss sell index-1")
                self.sell(fromStop=True)
        else:
            if todayPrice <= 0.6 * (BuyPrice - PredictedPrice):
                print("stop loss buy index-2")
                self.buy(fromStop=True)
        # lower is losing 1/4 what model predicted
        # losing 1/4 * predicted_pct
        # if is Short todayPrice >= BuyPrice + 1 /4 * predicted_pct
        # if long then  todayPrice <= BuyPrice - 1 /4 * predicted_pct
        # predicted_pct
        # 1 - (BuyPrice - PredictedPrice)
        predicted_pct = 1-(BuyPrice - PredictedPrice)
        if not isShort:
            if todayPrice <= BuyPrice - (1 / 4) * predicted_pct * BuyPrice:
                print("stop loss sell index-3")
                self.sell(fromStop=True)
        else:
            if todayPrice >= BuyPrice + (1 / 4) * predicted_pct * BuyPrice:
                print(4)
                print("stop loss sell index-4")
                self.buy(fromStop=True)
                print("after loss amount:")
                print(self.GetStockAmount())
        
    def scedule(self):
        schedule.every(self.secondsWaitingForStopLoss).seconds.do(
            self.DecideStopLoss)
        # schedule.every().day.at("16:35").do(self.DecideBuyOrSell)
        # schedule.every().day.at("20:00").do(self.DecideBuyOrSell)
        for time in self.buyTimes:
            schedule.every().day.at(time).do(self.DecideBuyOrSell)

    def run_pending(self):
        schedule.run_pending()
