import re
import time
import os

import requests
import json
import pandas as pd
from datetime import datetime
import numpy as np


class CryptoCompareAPI():

    def __init__(self):
        self.url = 'https://min-api.cryptocompare.com/data'

    def _safeRequest(self, url):
        while True:
            try:
                response = requests.get(url)
            except Exception as e:
                print(f'Connection Failed: {e}. Reconnecting...')
                time.sleep(1)
            else:
                break
        resp = response.json()
        if response.status_code != 200:
            raise Exception(resp)
        data = resp['Data']
        return data

    def _setBaseUrl(self, fsym, tsym, freq, e):
        '''return correct service url based on timeframe set

        Parameters
        ----------
            fsym: ticker
            tsym: base
            freq: '1m', '2h', '3d'
            e: exchange (default:CCCAGG)

        Raise
        -----
            ValueError

        Returns
        -------
        str
            a string of corresponding service url from cryptoCompare.com
        '''
        fsym = fsym.upper()
        tsym = tsym.upper()
        agg = re.findall(r"\d+", freq)[0]
        freq = re.findall(r"[a-z]", freq)[0]
        if freq == 'd':
            base_url = f"/histoday?fsym={fsym}&tsym={tsym}"
        elif freq == 'h':
            base_url = f"/histohour?fsym={fsym}&tsym={tsym}"
        elif freq == 'm':
            base_url = f"/histominute?fsym={fsym}&tsym={tsym}"
        else:
            raise ValueError('frequency', freq, 'not supported')
        base_url += f'&aggregate={agg}'  # aggragate
        base_url += f'&e={e}'  # exchange
        return base_url


    def getHistoData(self, fsym, tsym, freq, e='CCCAGG', start_time=None, end_time=None, limit=None):
        """
            fsym: ticker
            tsym: base
            freq: '1m', '2h', '3d'
            start_time: string datetime format
            end_time: string datetime format
            limit: number of candles
            e: exchange (default:CCCAGG)
        """
        base_url = self._setBaseUrl(fsym, tsym, freq, e)
        if start_time != None and end_time != None and limit == None:
            base_url += f'&limit={2000}'
            start_timestamp = int(pd.to_datetime(start_time).timestamp())
            end_timestamp = int(pd.to_datetime(end_time).timestamp())
            query_url = base_url + f'&toTs={end_timestamp}'
            df = pd.DataFrame(self._safeRequest(self.url+query_url))
            if len(df) == 0:
                raise Exception(f'No Data Fetched with {self.url + query_url}')
            while True:
                earliest_timestamp = df.iloc[0]['time']
                if earliest_timestamp <= start_timestamp:
                    df = df[df['time'] >= start_timestamp]
                    break
                else:
                    query_url = base_url + f'&toTs={earliest_timestamp}'
                    query_df = pd.DataFrame(
                        self._safeRequest(self.url + query_url))
                    if len(query_df) == 0:
                        request_time = datetime.utcfromtimestamp(
                            start_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                        earlies_time = datetime.utcfromtimestamp(
                            earliest_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                        print(
                            f"Request from {request_time}. But Available from {earlies_time}")
                        break
                    else:
                        df = query_df.append(df.iloc[1:], ignore_index=True)
            return df
        elif end_time != None and limit != None and start_time == None:
            end_timestamp = int(pd.to_datetime(end_time).timestamp())
            base_url += f'&limit={limit}'  # limit
            query_url = base_url + f'&toTs={end_timestamp}'  # until
            return pd.DataFrame(self._safeRequest(self.url + query_url))
        elif end_time == None and start_time == None and limit != None:
            base_url += f'&limit={limit}'  # limit
            return pd.DataFrame(self._safeRequest(self.url + base_url))
        else:
            raise ValueError(
                f"Can't do start_time={start_time}, end_time={end_time}, limit={limit}")


    def getTopListMCap(self, tsym, rank_from=None, rank_to=None, ascending=False, sign=False):
        '''
            tsym: The currency symbol to convert into
            limit: The number of coins to return in the toplist, default 10, min 10, max 100
            page: The pagination for the request.
            ascending: Boolean
            sign: Boolean, If set to true, the server will sign the requests

            TODO: add ascending
        '''
        base_url = '/top/mktcapfull?'
        tsym = tsym.upper()
        base_url += f'&tsym={tsym}'

        if sign is True:
            base_url += f'&sign={sign}'

        if rank_from == None and rank_to == None:
            page = 0
            base_url += f'&limit={50}'
            query_url = base_url + f'&page={page}'
            df = pd.DataFrame(self._safeRequest(self.url + query_url))
            df = df.dropna()

            if len(df) == 0:
                raise Exception(f'No Data Fetched with {self.url + query_url}')
            while True:
                page += 1
                query_url = base_url + f'&page={page}'
                query_df = pd.DataFrame(
                    self._safeRequest(self.url + query_url))
                query_df = query_df.dropna()
                if len(query_df) == 0:
                    break
                else:
                    df = df.append(query_df, ignore_index=True)

            df = pd.DataFrame([df['RAW'][x][tsym] for x in range(len(df))])
            df.index += 1
            return df

        elif rank_to!=None:
            if rank_to > 50:
                page = 0
                query_url = base_url + f'&limit={50}' + f'&page={page}'
                df = pd.DataFrame(self._safeRequest(self.url + query_url))
                df = df.dropna()
                for i in range((rank_to//50)-1):
                    page = i
                    query_url = base_url + f'&limit={50}' + f'&page={page}'
                    query_df = pd.DataFrame(self._safeRequest(self.url + query_url))
                    query_df = query_df.dropna()
                    df = df.append(query_df, ignore_index=True)
                if rank_to%50 != 0:
                    page += 1

                    query_url = base_url + f'&limit={rank_to%50}' + f'&page={page}'

                    query_df = pd.DataFrame(self._safeRequest(self.url + query_url))

                    query_df = query_df.dropna()
                    df = df.append(query_df, ignore_index=True)
                df = pd.DataFrame([df['RAW'][x][tsym] for x in range(len(df))])
                df.index += 1
                if rank_from==None:
                    return df
                else:
                    return df.loc[rank_from:]
            else:
                query_url = base_url + f'&limit={rank_to}'
                df = pd.DataFrame(self._safeRequest(self.url + query_url))
                df = pd.DataFrame([df['RAW'][x][tsym] for x in range(len(df))])
                df.index += 1
                if rank_from==None:
                    return df
                else:
                    return df.loc[rank_from:]
        


def unix2date(unix, fmt="%Y-%m-%d %H:%M:%S"):
    """
        Convert unix epoch time 1562554800 to
        datetime with format
    """
    date = datetime.utcfromtimestamp(unix)
    return date.strftime(fmt)


def date2unxi(date, fmt="%Y-%m-%d %H:%M:%S"):
    """
        Convert datetime with format to 
        unix epoch time 1562554800
    """
    return int(time.mktime(time.strptime(date, fmt)))


def cc2bt(df):
    """Convert CryptoCompare data to Backtrader data
    """
    df['datetime'] = df['time'].apply(unix2date
                                      )
    df.drop(columns=['time'], inplace=True)
    df.rename(columns={'volumefrom': 'volume',
                       'volumeto': 'baseVolume'}, inplace=True)
    return df


def topMCapCleanData(df):
    '''Clean up market cap data
    '''
    new_df = df[['FROMSYMBOL', 'TOSYMBOL', 'MKTCAP', 'PRICE',
                'VOLUME24HOURTO', 'SUPPLY', 'CHANGEPCT24HOUR']]
    return new_df


if __name__ == "__main__":
    cc_api = CryptoCompareAPI()
    DATA_DIR = './data'

    df = cc_api.getHistoData('BTC', 'USDT', '1h', start_time="2020-01-01", end_time="2020-04-01", e='binance')
    df = cc2bt(df)
    with open(os.path.join(DATA_DIR, "BTC_USDT_1h.csv"), 'w') as csv_file:
      df.to_csv(csv_file, index=False)


    # # case 1: get all coin data
    # df = cc_api.getTopListMCap('usd')
    # df = topMCapCleanData(df)
    # with open(os.path.join(DATA_DIR, 'all_coin_market_cap.csv'), 'w') as csv_file:
    #     df.to_csv(csv_file)

    # # case 2: get top # coin data
    # df = cc_api.getTopListMCap('usd', rank_to=120)
    # df = topMCapCleanData(df)
    # with open(os.path.join(DATA_DIR, 'coin_market_cap_top120.csv'), 'w') as csv_file:
    #     df.to_csv(csv_file)


    # # case 3: get coin rank from 20 - 30 based on MCap
    # df = cc_api.getTopListMCap('usd', rank_from=20, rank_to=140)
    # df = topMCapCleanData(df)
    # with open(os.path.join(DATA_DIR, 'coin_market_cap_rank20_140.csv'), 'w') as csv_file:
    #     df.to_csv(csv_file)


