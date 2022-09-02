from quant_mock._market import *

import pandas as pd
import matplotlib.pyplot as plt


class Account(object):
    def __init__(self,
                 market_data: dict,
                 start_time:dt.datetime,
                 balance: int
                 ) -> None:
        self.market = Market(
            market_data=market_data,
            start_time=start_time
        )
        self.capital = balance
        self.balance = balance
        self.position = {}
        for key in self.market._market_data.keys():
            self.position[key] = [0, 0]
        self.history = pd.DataFrame(
            columns=['date', 'name', 'change', 'position', 'price', 'balance', 'asset'])
        _revenue_details = ['asset','rate','balance']
        _revenue_details.extend([name for name in self.position.keys()])
        self.revenue_details = pd.DataFrame(columns=_revenue_details)

    def revenue_plot(self):
        plt.xlabel("Date")
        plt.ylabel("Rate")
        ax = plt.gca()
        ax.xaxis.set_major_locator(md.WeekdayLocator(byweekday=md.MO))
        ax.xaxis.set_major_formatter(md.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_minor_locator(md.DayLocator())
        plt.plot(self.revenue_details.index,self.revenue_details.rate)
        plt.ylim(
            min(self.revenue_details.rate)-0.02,
            max(self.revenue_details.rate)+0.01
        )
        plt.hlines(0,
            self.revenue_details.index[0]-dt.timedelta(3),
            self.revenue_details.index[-1]+dt.timedelta(3),
            linestyles=":",
            colors=['red']
            )
        plt.gcf().autofmt_xdate()
        plt.show()

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
        asset_dict.update({'rate':asset_dict['asset']/self.capital-1})
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
