from QuantMock._market import *
from QuantMock._trader import *


class SimpleGridTrading(object):
    def __init__(self,
                 account: Account,
                 grid: list,
                 batch: int,
                 duration: int) -> None:
        self.account = account
        self.grid = grid
        self.batch = batch
        self.duration = duration

    def run(self) -> None:
        grid_refers = {}
        for _ in range(self.duration):
            for k,v in self.account.market._market_data.items():
                # TODO
                pass
