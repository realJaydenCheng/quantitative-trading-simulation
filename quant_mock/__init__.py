from quant_mock._market import *
from quant_mock._trader import *
import numpy as np
import pandas as pd


class SimpleGridTrade(object):
    def __init__(self,
                 account: Account,
                 grid: list,
                 batch: int,
                 duration: int,
                 establish: dict) -> None:
        self.account = account
        self.grid = np.array(grid)
        self.batch = batch
        self.duration = duration
        self._grid_refers = {}
        self._grid_change = {}
        self.account.establish(establish)
        self.labels = labels = [i for i in range(1,len(self.grid))]
        for k, v in self.account.market._market_data.items():
            self._grid_refers[k] = (
                0,
                v.closed[self.account.market.today]
            )
            self._grid_change[k] = (0,0)
        self.account.next_day()

    def run(self) -> None:
        for _ in range(self.duration):
            for k, v in self.account.market._market_data.items():
                if self.account.market.today not in v.index:
                    continue
                self._grid_refers[k] = (
                    self._grid_refers[k][-1],
                    v.closed[self.account.market.today]
                )
                _grid_change_temp = (
                    self._grid_change[k][-1],
                    pd.cut([v.open[self.account.market.today]],self.grid*self._grid_refers[k][0],labels=self.labels)[0]
                )
                if np.isnan(self._grid_change[k][-1]):
                    print(f"{k} out of range at {self.account.market.today}")
                if sorted(_grid_change_temp) == self._grid_change[k]:
                    continue
                else :
                    if _grid_change_temp[-1] == _grid_change_temp[0]:
                        continue
                    elif _grid_change_temp[-1] > _grid_change_temp[0]:
                        self.account.sell(k,self.batch)
                    elif _grid_change_temp[-1] < _grid_change_temp[0]:
                        self.account.buy(k,self.batch)
                self._grid_change[k] = _grid_change_temp
            self.account.next_day()
                    
