from QuantMock._market import *

import pandas as pd

class Account(object):
    def __init__(self,
        market:Market,
        balance:int
    ) -> None:
        self.market = market
        self.balance = balance
        self.position = {}
        for key in market._market_data.keys():
            self.position[key] = 0
        self.history = pd.DataFrame(columns=['date','name','change','position','price','balance'])

    def buy(self,name:str,value:int)->bool:
        if value > self.balance:
            return False
        if self.market.today not in self.market[name].index:
            return False
        count = value // (self.market[name].low[self.market.today])
        self.position[name] += count
        self.balance -= count * self.market[name].low[self.market.today]
        self.history = self.history.append({
            'date':self.market.today,
            'name':name,
            'change':+count,
            'position':self.position[name],
            'price':self.market[name].low[self.market.today],
            'balance':self.balance
        },ignore_index=True)
        return True

    def sell(self,name:str,value:int)->bool:
        if self.market.today not in self.market[name].index:
            return False
        count = value // (self.market[name].high[self.market.today])
        if count > self.position[name]:
            return False
        self.position[name] -= count
        self.balance += count * self.market[name].high[self.market.today]
        self.history = self.history.append({
            'date':self.market.today,
            'name':name,
            'change':-count,
            'position':self.position[name],
            'price':self.market[name].high[self.market.today],
            'balance':self.balance
        },ignore_index=True)
        return True

    def establish(self,position:dict):
        for k,v in position.items():
            self.buy(k,v)

    @property
    def asset(self)->pd.DataFrame:
        asset_dict = {'balance':self.balance}
        asset_dict.update(self.position)
        return pd.DataFrame(asset_dict)