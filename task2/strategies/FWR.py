
import os
import datetime
import sys

import backtrader as bt
import backtrader.indicator as btind

import pandas as pd
import matplotlib.pyplot as plt


class FWR(bt.Strategy):
    params = (
        ('stop_loss', 0.02),
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

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

        self.first_high = self.datahigh[-3] > self.datahigh[-4]
        self.second_high = self.datahigh[-2] > self.datahigh[-3]
        self.third_high = self.datahigh[-1] > self.datahigh[-2]
        self.fourth_high = self.datahigh[0] > self.datahigh[-1]

        self.buysig = (self.datas[0].datetime[0] > self.datas[0].datetime[-4]
                       ) & self.first_high & self.second_high & self.third_high & self.fourth_high

        self.first_low = self.datalow[-3] < self.datalow[-4]
        self.second_low = self.datalow[-2] < self.datalow[-3]
        self.third_low = self.datalow[-1] < self.datalow[-2]
        self.fourth_low = self.datalow[0] < self.datalow[-1]

        self.sellsig = (self.datas[0].datetime[0] > self.datas[0].datetime[-4]
                       ) & self.first_low & self.second_low & self.third_low & self.fourth_low
        
        self.stoplosssig = False

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.buysig:

                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()

                self.buyprice = self.order.executed.price

        else:
            
            if self.dataclose[0] < self.buyprice*(1-self.p.stop_loss):
                self.stoplosssig = True

            if self.sellsig or self.stoplosssig:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()
