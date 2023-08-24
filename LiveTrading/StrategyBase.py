from LiveTrading.DeribitWS import DeribitWS
import pandas as pd
import numpy as np
import datetime as dt
import json
import time


class StrategyBase:

    def __init__(self, client_id, client_secret, instrument, timeframe,
                 trade_capital, max_holding, ub_mult, lb_mult, live=False):

        self.WS = DeribitWS(client_id, client_secret, live)
        self.instrument = instrument
        self.timeframe = timeframe
        self.trade_capital = trade_capital

        self.ub_mult = ub_mult
        self.lb_mult = lb_mult
        self.max_holding = max_holding
        self.max_holding_limit = max_holding

        #trade variables
        self.open_pos = False
        self.stop_price = None
        self.target_price = None
        self.direction = None
        self.fees = 0
        self.open_price = None
        self.close_price = None

        self.trades = {'open_timestamp': [], 'close_timestamp': [],
                       'open': [], 'close': [], 'fees': [], 'direction': []}


    @staticmethod
    def json_to_dataframe(json_resp):
        res = json_resp['result']
        df = pd.DataFrame(res)
        df['ticks_'] = df.ticks / 1000
        df['timestamp'] = [dt.datetime.utcfromtimestamp(date) for date in df.ticks_]
        return df

    @staticmethod
    def utc_times_now():
        string_time = time.strftime("%Y %m %d %H %M %S").split(' ')
        int_time = list(map(int, string_time))
        now = dt.datetime(int_time[0],
                          int_time[1],
                          int_time[2],
                          int_time[3],
                          int_time[4],
                          int_time[5]).timestamp() * 1000
        return now 

    def open_long(self):
        trade_resp = self.WS.market_order(self.instrument, self.trade_capital, 'long')
        print(trade_resp)
        if 'result' in trade_resp.keys():
            self.open_pos = True
            self.open_price = trade_resp['result']['order']['average_price']
            self.target_price = self.open_price * self.ub_mult
            self.stop_price = self.open_price * self.lb_mult
            self.direction = 1
            print(trade_resp['result']['order'])
            # self.fees += trade_resp['result']['order']['commission']
            self.trades['open_timestamp'].append(dt.datetime.now())
            print(f'opening long at {self.open_price}',
                    f'with stop price {self.stop_price} and target {self.target_price}')

        else:
            print(trade_resp['error'])


    def open_short(self):
        trade_resp = self.WS.market_order(self.instrument, self.trade_capital, 'short')
        if 'result' in trade_resp.keys():
            self.open_pos = True
            self.open_price = trade_resp['result']['order']['average_price']
            self.target_price = self.open_price * self.lb_mult
            self.stop_price = self.open_price * self.ub_mult
            self.direction = -1
            # self.fees += trade_resp['result']['order']['commission']
            self.trades['open_timestamp'].append(dt.datetime.now())
            print(f'opening short at {self.open_price}',
                  f'with stop price {self.stop_price} and target {self.target_price}')
        else:
            print(trade_resp['error'])


    def reset_vars(self):
        self.open_pos = False
        self.target_price = None
        self.stop_price = None
        self.direction = None
        self.fees = 0
        self.open_price = None
        self.max_holding = self.max_holding_limit
        self.close_price = None

    def close_position(self):
        if self.direction == 1:
            close_resp = self.WS.market_order(self.instrument, self.trade_capital, 'short')
            if 'result' in close_resp.keys():
                self.close_price = close_resp['result']['order']['average_price']
                self.trades["open"].append(self.open_price)
                self.trades["close"].append(self.close_price)
                self.trades["direction"].append(self.direction)
                # self.trades["fees"].append(self.fees + close_resp['result']['order']['commission'])
                self.trades['close_timestamp'].append(dt.datetime.now())
                print(f'closing long at {self.close_price}',
                        f'for a {round(self.close_price / self.open_price - 1, 5) * 100}% return')
                self.reset_vars()
            else:
                print(close_resp['error'])

        if self.direction == -1:
            close_resp = self.WS.market_order(self.instrument, self.trade_capital, 'long')
            if 'result' in close_resp.keys():
                self.close_price = close_resp['result']['order']['average_price']
                self.trades["open"].append(self.open_price)
                self.trades["close"].append(self.close_price)
                self.trades["direction"].append(self.direction)
                # self.trades["fees"].append(self.fees + close_resp['result']['order']['commission'])
                self.trades['close_timestamp'].append(dt.datetime.now())
                print(f"closing short at {self.close_price}",
                        f"for a {round(-1* (self.close_price/self.open_price - 1) * 100 , 5)}% return")
                self.reset_vars()
            else:
                print(close_resp['error'])

    def monitor_open(self, price):
        if price >= self.target_price and self.direction == 1:
            self.close_position()
            print('long target hit')
        elif price <= self.stop_price and self.direction == 1:
            self.close_position()
            print('long stop hit')
        elif price <= self.target_price and self.direction == -1:
            self.close_position()
            print('short target hit')
        elif price >= self.stop_price and self.direction == -1:
            self.close_position()
            print('short stop hit')
        elif self.max_holding <= 0:
            self.close_position()
            print("max holding time exceeded closing position")
        else:
            self.max_holding = self.max_holding - 1