from quant_mock._market import *

import pandas as pd


class Account(object):
    def __init__(self,
                 market: Market,
                 balance: int
                 ) -> None:
        self.market = market
        self.balance = balance
        self.position = {}
        for key in market._market_data.keys():
            self.position[key] = [0, 0]
        self.history = pd.DataFrame(
            columns=['date', 'name', 'change', 'position', 'price', 'balance', 'asset'])
        _revenue_details = ['asset','balance']
        _revenue_details.extend([name for name in self.position.keys()])
        self.revenue_details = pd.DataFrame(columns=_revenue_details)

    def revenue_plot():
        pass

    def buy(self, name: str, value: int) -> bool:
        if value > self.balance:
            return False
        if self.market.today not in self.market[name].index:
            return False
        count = value // (self.market[name].low[self.market.today])
        self.position[name] = [self.position[name][0] +
            count, self.market[name].high[self.market.today]]
        self.balance -= count * self.market[name].low[self.market.today]
        self.history = self.history.append({
            'date': self.market.today,
            'name': name,
            'change': +count,
            'position': self.position[name][0],
            'price': self.market[name].low[self.market.today],
            'balance': self.balance,
            'asset': self.balance + sum([
                l[0]*l[1] for l in self.position.values()
            ])
        }, ignore_index=True)
        return True

    def sell(self, name: str, value: int) -> bool:
        if self.market.today not in self.market[name].index:
            return False
        count = value // (self.market[name].high[self.market.today])
        if count > self.position[name][0]:
            return False
        self.position[name] = [self.position[name][0] -
            count, self.market[name].high[self.market.today]]
        self.balance += count * self.market[name].high[self.market.today]
        self.history = self.history.append({
            'date': self.market.today,
            'name': name,
            'change': -count,
            'position': self.position[name][0],
            'price': self.market[name].high[self.market.today],
            'balance': self.balance,
            'asset': self.balance + sum([
                l[0]*l[1] for l in self.position.values()
            ])
        }, ignore_index=True)
        return True

    def establish(self, position: dict):
        for k, v in position.items():
            self.buy(k, v)

    def next_day(self):
        asset_dict = {
            'balance': self.balance,
            'asset': self.balance + sum([
                l[0]*l[1] for l in self.position.values()
            ])
        }
        asset_dict.update(dict([(k,v[0]) for k,v in self.position.items()]))
        self.revenue_details = pd.concat([
            self.revenue_details,
            pd.DataFrame(asset_dict,index=[self.market.today])
            ])
        self.market.next_day()

    @property
    def asset(self) -> pd.DataFrame:
        asset_dict = {
            'balance': self.balance,
            'asset': self.balance + sum([
                l[0]*l[1] for l in self.position.values()
            ])
        }
        asset_dict.update(dict([(k,v[0]) for k,v in self.position.items()]))
        return pd.DataFrame(asset_dict,index=[0])
