import math
import os
import datetime
import sys

import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.indicator as btind
import pandas as pd
import matplotlib.pyplot as plt

from report import PerformanceReport
from strategies.SMACross import SMACross
from strategies.EMACross import EMACross
from strategies.FWR import FWR
from strategies.IchimokuStrategy import IchimokuStrat

datadir = './data'
logdir = './log'
reportdir = './report'
datafile = 'BTC_USDT_1h.csv'
from_datetime = '2020-01-01 00:00:00'
to_datetime = '2020-04-01 00:00:00'

if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(IchimokuStrat)

    # Feed data
    data = pd.read_csv(os.path.join(datadir, datafile),
                       index_col='datetime', parse_dates=True)
    data = data.loc[(data.index >= pd.to_datetime(from_datetime))
                    & (data.index <= pd.to_datetime(to_datetime))]
    datafeed = btfeeds.PandasData(dataname=data)

    # Add the Data Feed to Cerebro
    cerebro.adddata(datafeed)

    # cerebro.resampledata(datafeed, timeframe=bt.TimeFrame.Weeks, compression=1)

    # Set our desired cash start
    cerebro.broker.setcash(100000)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.PercentSizer, percents=99)

    # Set the commission
    cerebro.broker.setcommission(commission=0.001)

    # config log file and fig file names
    params_lst = [str(v)
                  for k, v in cerebro.strats[0][0][0].params.__dict__.items()
                  if not k.startswith('_')]
    resfile = '_'.join([
        os.path.splitext(datafile)[0],
        cerebro.strats[0][0][0].__name__,
        '_'.join(params_lst), from_datetime.split(" ")[0], to_datetime.split(" ")[0]])
    logfile = resfile + '.csv'
    cerebro.addwriter(bt.WriterFile, out=os.path.join(
        logdir, logfile), csv=True)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio,
                        _name="mySharpe",
                        timeframe=bt.TimeFrame.Months)
    cerebro.addanalyzer(bt.analyzers.DrawDown,
                        _name="myDrawDown")
    cerebro.addanalyzer(bt.analyzers.AnnualReturn,
                        _name="myReturn")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer,
                        _name="myTradeAnalysis")
    cerebro.addanalyzer(bt.analyzers.SQN,
                        _name="mySqn")

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    plt.rcParams['figure.figsize'] = [13.8, 10]
    fig = cerebro.plot(style='candlestick', barup='green', bardown='red')
    figfile = resfile + '.png'
    # fig[0][0].savefig(os.path.join(reportdir, figfile), dpi=480)

    strat = cerebro.runstrats[0][0]
    reportfile = resfile + '.pdf'
    PerformanceReport(
        strat, outputdir=reportdir, infilename=datafile, user='Bowen', memo='').generate_pdf_report(filename=reportfile)

