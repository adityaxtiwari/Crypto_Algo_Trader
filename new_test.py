from LiveTrading.DeribitWS import DeribitWS
import numpy as np
import datetime as dt
import time
import json

with open('auth_creds.json') as j:
    creds = json.load(j)

client_id = creds['paper']['client_id']
client_secret = creds['paper']['client_secret']


class RandomAlgo:

    def __init__(self, client_id, client_secret,
                 instrument, trade_capital,
                 live=False):

        self.WS = DeribitWS(client_id, client_secret, live)
        self.instrument = instrument
        self.trade_capital = trade_capital


    def run(self, endtime):
        while True:
            timenow = dt.datetime.now()
            side = np.random.choice([-1, 1])
            if timenow.second == 0:
                if side == 1:
                    trade_resp = self.WS.market_order(self.instrument, self.trade_capital, 'long')
                    print('long trade entered')
                else:
                    trade_resp = self.WS.market_order(self.instrument, self.trade_capital, 'short')
                    print('short trade entered')
            time.sleep(1)
            if timenow >= endtime:
                break



if __name__ == '__main__':
    Ralgo = RandomAlgo(client_id, client_secret, 'BTC-PERPETUAL', 100, live=False)

    endtime = dt.datetime(2023, 8, 7, 20, 30) #change this to a suitable datetime

    Ralgo.run(endtime)