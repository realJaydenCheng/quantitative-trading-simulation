import QuantMock as qm
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
# import seaborn as sns

TEST_DAYS = 240
START_DAY = dt.datetime(2022, 1, 4)
CAPITAL = 5000000


market_data = {
    'SSEA': pd.read_csv('./ssea.csv', index_col='date', parse_dates=True),
    'BTC': pd.read_excel('./Bitcoin.xlsx', 'Bitcoin', index_col='date')
}

market = qm.Market(
    market_data=market_data,
    start_time=START_DAY
)

account = qm.Account(market, CAPITAL)
trader = qm.SimpleGridTrade(
    account=account,
    grid=[0.97, 0.98, 0.99, 1, 1.01, 1.02, 1.03],
    batch=50000,
    duration=TEST_DAYS,
    establish={
        'SSEA': 1500000,
        'BTC': 500000
    }
)

trader.run()
print(account.history)
# market.candle_plot('BTC',START_DAY)
# market.volume_plot('BTC',START_DAY)
