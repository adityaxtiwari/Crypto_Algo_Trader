from LiveTrading.StrategyBase import StrategyBase
import pandas as pd
import numpy as np
import datetime as dt
import time
import json

with open('auth_creds.json') as j:
    creds = json.load(j)

client_id = creds['paper']['client_id']
client_secret = creds['paper']['client_secret']


class PolyTest(StrategyBase):

    def __init__(self, client_id, client_secret, instrument, timeframe,
                 trade_capital, max_holding, ub_mult, lb_mult,
                 entry_cond, lookback, n, live=False):

        super().__init__(client_id, client_secret, instrument, timeframe,
                         trade_capital, max_holding, ub_mult, lb_mult,
                         live)

        self.entry_cond = entry_cond
        self.lookback = lookback
        self.n = n
        self.delta = 60000

    def generate_signal(self, data):
        y = data.close.values.reshape(-1, 1)
        t = np.arange(len(y))
        X = np.c_[np.ones_like(y), t, t ** 2]
        betas = np.linalg.inv(X.T @ X) @ X.T @ y
        new_vals = np.array([1, t[-1] + self.n, (t[-1] + self.n) ** 2])
        pred = new_vals @ betas
        print(f"pred: {int(pred)}, last: {int(y[-1])}")
        if (pred / y[-1] - 1) > self.entry_cond:
            return 1
        elif (pred / y[-1] - 1) < -self.entry_cond:
            return -1
        else:
            return 0

    def get_data(self):
        end = self.utc_times_now()
        start = end - self.delta*self.lookback
        json_resp = self.WS.get_data(self.instrument, start, end, self.timeframe)
        if 'error' in json_resp.keys():
            print(json_resp['error'])
            return False, False
        elif 'result' in json_resp.keys():
            data = self.json_to_dataframe(json_resp)
            return True, data
        else:
            return False, False


    def run(self, endtime):
        print(f"started strategy at {dt.datetime.now()}")
        while True:
            timenow = dt.datetime.now()
            if timenow.second == 0:
                t = time.time()
                good_call, data = self.get_data()
                if not good_call:
                    time.sleep(1)
                    continue
                last_price = data.close.values[-1]
                signal = self.generate_signal(data)

                if signal == 1 and self.open_pos is False:
                    self.open_long()
                    print(f"took {time.time()-t} seconds to execute")
                elif signal == -1 and self.open_pos is False:
                    self.open_short()
                    print(f"took {time.time() - t} seconds to execute")
                elif self.open_pos:
                    self.monitor_open(last_price)
                else:
                    pass

                time.sleep(1)

            if timenow >= endtime:
                print(f"Exiting strategy at {dt.datetime.now()}")
                if self.open_pos:
                    self.close_position()
                break




if __name__ == '__main__':
    instrument = 'BTC-PERPETUAL'
    timeframe = '1'
    trade_capital = 100
    ub_mult = 1.05
    lb_mult = 0.95
    max_holding = 2
    entry_cond = 0.0001
    n = 3
    lookback = 60

    strat = PolyTest(client_id, client_secret, instrument, timeframe, trade_capital,
                     max_holding, ub_mult, lb_mult, entry_cond, lookback, n, live=False)

    endtime = dt.datetime(2023, 8, 24, 21, 47)

    strat.run(endtime)
