import pandas as pd
import datetime as dt
import numpy as np
import matplotlib.dates as md
import matplotlib.pyplot as plt


class Market(object):
    def __init__(self,
        market_data: dict = None,
        start_time: dt.datetime = dt.datetime.today()
    ) -> None:
        self._market_data = market_data
        self.today = start_time

    def next_day(self) -> None:
        self.today += dt.timedelta(1)

    def __getitem__(self, key) -> pd.Series:
        return self._market_data[key]

    def set_item(self, name: str, data: pd.DataFrame) -> None:
        self._market_data[name] = data

    def candle_plot(self, name: str):
        plt.xlabel("Date")
        plt.ylabel("Price")
        ax = plt.gca()
        ax.xaxis.set_major_locator(md.WeekdayLocator(byweekday=md.MO))
        ax.xaxis.set_major_formatter(md.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_minor_locator(md.DayLocator())
        colors_bool = self[name].closed >= self[name].open
        colors = np.zeros(colors_bool.size, dtype="U5")
        colors[:] = "blue"
        colors[colors_bool] = "white"
        edge_colors = np.zeros(colors_bool.size, dtype="U1")
        edge_colors[:] = "b"
        edge_colors[colors_bool] = "r"
        plt.bar(
            self[name].index, 
            self[name].closed - self[name].open, 
            0.8, 
            bottom=self[name].open, 
            color=colors,
            edgecolor=edge_colors, 
            zorder=3
        )
        plt.vlines(
            self[name].index, 
            self[name].low,self[name].high, 
            color=edge_colors
        )
        plt.gcf().autofmt_xdate()
        plt.show()

    def volume_plot(self, name: str):
        plt.xlabel("Date")
        plt.ylabel("Volume")
        ax = plt.gca()
        ax.xaxis.set_major_locator(md.WeekdayLocator(byweekday=md.MO))
        ax.xaxis.set_major_formatter(md.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_minor_locator(md.DayLocator())
        plt.bar(
            self[name].index,
            self[name].volume,
            color='c'
        )
        plt.gcf().autofmt_xdate()
        plt.show()
