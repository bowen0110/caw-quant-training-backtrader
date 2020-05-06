import backtrader as bt
import backtrader.indicators as btind
import backtrader.feeds as btfeeds

import backtrader as bt
import backtrader.feeds as btfeeds
import pandas as pd
import matplotlib as plt

import os

datadir = './data'  # data path
logdir = './log'  # log path
reportdir = './report'  # report path
datafile = 'BTC_USDT_1h.csv'  # data file
logfile = 'BTC_USDT_1h_SMACross_10_20_2020-01-01_2020-04-01.csv' # log file
figfile = 'BTC_USDT_1h_SMACross_10_20_2020-01-01_2020-04-01.png' # fig file
from_datetime = '2020-01-01 00:00:00'  # start time
to_datetime = '2020-04-01 00:00:00'  # end time

# Data Feed
class MyStrategy(bt.Strategy):
    params = dict(period=20)

    def __init__(self):

        sma = btind.SimpleMovingAverage(self.data, period=self.params.period)
        print (self.data.lines.close[0])


cerebro = bt.Cerebro()

data = pd.read_csv(os.path.join(datadir, datafile),
                       index_col='datetime', parse_dates=True)

datafeed = bt.feeds.PandasData(dataname=data)

cerebro.adddata(datafeed)
cerebro.addstrategy(MyStrategy, period=30)

 # Set our desired cash start
cerebro.broker.setcash(10000)

cerebro.run()