import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

# Import the backtrader platform
import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.indicators as btind

import pandas as pd
import matplotlib.pyplot as plt

datadir = './data'  # data path
logdir = './log'  # log path
reportdir = './report'  # report path
tradingpair = 'BTC_USDT' # trading pair
freq  = '1h' # trading frequency
datafile = f'{tradingpair}_{freq}.csv'  # data file
from_datetime = '2020-01-01 00:00:00'  # start time
to_datetime = '2020-04-01 00:00:00'  # end time


# Create a Stratey
class EMACross(bt.Strategy):
    params = (
        ('pfast', 50),
        ('pslow', 200),
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # Add a MovingAverageSimple indicator
        self.ema1 = btind.ExponentialMovingAverage(self.datas[0], period=self.p.pfast)
        self.ema2 = btind.ExponentialMovingAverage(self.datas[0], period=self.p.pslow)
        self.crossover = btind.CrossOver(self.ema1, self.ema2)  # crossover signal

        
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.crossover > 0:

                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()

        else:

            if self.crossover < 0:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()


if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(EMACross)

    # Feed data
    data = pd.read_csv(os.path.join(datadir, datafile),
                       index_col='datetime', parse_dates=True)
    data = data.loc[(data.index >= pd.to_datetime(from_datetime))
                    & (data.index <= pd.to_datetime(to_datetime))]
    datafeed = bt.feeds.PandasData(dataname=data)

    # Add the Data Feed to Cerebro
    cerebro.adddata(datafeed)

    # Set our desired cash start
    cerebro.broker.setcash(10000)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.PercentSizer, percents=99)

    # Set the commission
    cerebro.broker.setcommission(commission=0.001)

    # config log file and fig file names
    strategy_name = cerebro.strats[0][0][0].__name__
    pfast = cerebro.strats[0][0][0].params.__dict__['pfast']
    pslow = cerebro.strats[0][0][0].params.__dict__['pslow']
    logfile = f'{tradingpair}_{freq}_{strategy_name}_{pfast}_{pslow}_2020-01-01_2020-04-01.csv' # log file
    figfile = f'{tradingpair}_{freq}_{strategy_name}_{pfast}_{pslow}_2020-01-01_2020-04-01.png' # fig file

    # Add loger
    cerebro.addwriter(bt.WriterFile, out=os.path.join(
        logdir, logfile), csv=True)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Save report
    plt.rcParams['figure.figsize'] = [13.8, 10]
    fig = cerebro.plot(style='candlestick', barup='green', bardown='red')
    fig[0][0].savefig(os.path.join(reportdir, figfile), dpi=480)

