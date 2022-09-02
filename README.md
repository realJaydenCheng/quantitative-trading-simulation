
# 自定义策略的量化投资模拟-以网格策略为例

> 本文以及本账号中所有内容仅用于个人学习记录，均不构成任何投资的意见和建议，不代表任何投资暗示。市场有风险，投资需谨慎。

## 问题与输入输出

给定若干金融产品的若干日市场信息，实现模拟量化交易过程。

- 输入包括金融产品的**市场信息**与量化交易**策略**及其参数。
- 输出为**交易明细**与最终**资产情况**，并且完成可视化。

## 模拟程序与数据结构

将量化投资的过程简化后可抽象为两个主体：**投资者**与**市场**。

### 市场

市场中有各个金融产品的信息，根据**时间**不同会有着不同的表现（即同一种金融产品在不同时间下有不同的价格），具体的时间变化将在策略模拟时实现。对于市场而言，可绘制出K线图与交易量图。依题意，除了可视化和时间变化之外，市场不会单独脱离投资者发生变化，故将市场封装在投资者账户中。

### 投资者

本程序中的投资者账户是针对于某一市场而言的，市场将封装在账户中。可见此时的“投资者账户”已经远远超过真实账户的内容，甚至包含了市场，也许叫做“上下文context”或“环境environment”之类的名称更加合适，但我懒得改了orz。

投资者及其账户可以做出对某一市场中的产品做出**买卖**等动作。特殊的，初始购买即**建仓**行为一般在策略中作为例外处理，故实现中将其单独处理。对于交易情况，可以将买点卖点和收益曲线进行可视化。

### 数据结构

对于市场数据，以天为单位，有收盘价、开盘价、最高价、最低价、交易量的数据。具体是一个二维列表：

| date | closed | open | high | low | volume |
| -- | -- | -- | ------ | -- | ------------- |
| 20xx/xx/xx | xx | xx | xxx | x | xxxxxx |

对于交易明细，也是一个二位列表，字段有日期、金融产品、变化数量、剩余数量、单价、余额、资产总额：

| date | name | change | position | price | balance | asset |
| ---- | ----- | ----- | -------- | ----- | ------- | ----- |
| 20xx/xx/xx | yyyy | xx | xxx | x | xxxxxx | xx |

对于每日资产情况，字段有日期、资产总额、增长率、余额、各产品数量：

| date | asset | rate | balance | names... |
| ---- | ----- | ----- | -------- | ----- |
| 20xx/xx/xx | yyyy | xx | xxx | x1... |

## 模拟程序的实现

所有代码数据结构上依赖于pandas库的DataFrame数据结构。由于使用了`DataFrame.append`方法，建议版本号不要高于`1.4.3`。限于篇幅仅展示部分代码，完整代码点击文末**阅读原文**，访问Gitee开源仓库。

### 代码结构

所有代码编写在`quant_mock`的包中，其中`__init__`编写有包初始化和交易策略代码，`_market`编写有市场相关代码，`_trader`中编写投资者账户代码。

### 市场类

市场类中包含有一个字典，键值对分别是金融产品的名称和金融产品的数据。另外还有一个“今天”字段，用于记录模拟市场的时间。

```python
class Market(object):
    def __init__(self,market_data: dict = None,
                 start_time: dt.datetime = dt.datetime.today()
                 ) -> None:
        self._market_data = market_data
        self.today = start_time
```

金融产品数据访问频率较高，频繁调用`market._market_data[name`影响代码的整洁且罗嗦，通过`__getitem__`魔法方法简化访问，这样可以直接通过类实例访问到实例中的字典数据，就像这样：`market[name]`。

```python
class Market(object):
    def __getitem__(self, key) -> pd.Series:
        return self._market_data[key]
```

也可以在实例创建后添加金融产品。为了方便日期变动，单独创建了“下一天”方法：

```python
class Market(object):
    def next_day(self) -> None:
        self.today += dt.timedelta(1)

    def set_item(self, name: str, data: pd.DataFrame) -> None:
        self._market_data[name] = data
```

类中还包含画图的代码，其中蜡烛图参考了[1]。代码量较多，详见Gitee：

```python
class Market(object):
    def candle_plot(self, name: str, start_time: dt.datetime):
        pass

    def volume_plot(self, name: str, start_time: dt.datetime):
        pass
```

### 账户类

上文提到，市场被封装在账户中，故账户初始化时需要提供市场数据，且市场不再需要单独实例化。参数中，`start_time` 将作为市场的起始时间，并保存在`self.start_time`字段中便于后续的交易记录等实现。`balance`将作为起始的流动资金，`self.balance`是记录账户余额的字段，而`self.capital`将记录初始的资金,便于收益率的计算。`self.position`将读取`market_data`中的key，建立一个存储持仓状态的字典。`self.history`与`self.revenue_details`均为`pd.DataFrame`数据结构，分别记录交易明细和每日收益。

```python
class Account(object):
    def __init__(self, market_data: dict,
                 start_time:dt.datetime, balance: int
                 ) -> None:
        self.market = Market(market_data,start_time)
        self.start_time = start_time
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
```

买卖的代码相差不大，主要差别在于能否进行买卖的判定上。首先都是判断是否当日是否为交易日，然后在判断是否有足够的余额或者产品进行买卖，最后进行买卖和记录交易明细。

```python
class Account(object):
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
            'date': self.market.today,'name': name,
            'change': +count,'position': self.position[name][0],
            'price': self.market[name].low[self.market.today],
            'balance': self.balance,
            'asset': self.balance + sum([
                l[0]*l[1] for l in self.position.values()
            ])}, ignore_index=True)
        return True

    def sell(self, name: str, value: int) -> bool:
        if self.market.today not in self.market[name].index:
            return False
        count = value // (self.market[name].high[self.market.today])
        if count > self.position[name][0]:
            return False
        pass
        return True
```

建仓的代码是在买操作的代码基础上封装的：

```python
class Account(object):
    def establish(self, position: dict):
        for k, v in position.items():
            self.buy(k, v)
```

在后面策略的实现中，调用市场的`next_day`方法显得特别罗嗦，且不便完成对每日收益情况得到统计。于是在账户类中对市场类中的`next_day`方法进行封装，并增加记录每日收益的功能。

```python
class Account(object):
    def next_day(self):
        asset_dict = {'balance': self.balance,
            'asset': self.balance + sum([
                l[0]*l[1] for l in self.position.values()])}
        asset_dict.update(dict([(k,v[0]) for k,v in self.position.items()]))
        asset_dict.update({'rate':asset_dict['asset']/self.capital-1})
        self.revenue_details = pd.concat([self.revenue_details,
            pd.DataFrame(asset_dict,index=[self.market.today])])
        self.market.next_day()
```

更多的还有asset属性和绘图代码。assert属性为了在调试中方便查看当前收益情况所设置的。

```python
class Account(object):
    @property
    def asset(self) -> pd.DataFrame:
        asset_dict = {'balance': self.balance,
            'asset': self.balance + sum([
                l[0]*l[1] for l in self.position.values()] )}
        asset_dict.update(dict([(k,v[0]) for k,v in self.position.items()]))
        return pd.DataFrame(asset_dict,index=[0])

    def revenue_plot(self):
        pass

    def trade_details_plot(self,name:str):
        pass
```

### 策略类

策略类代码并不提供具体策略，而是提供了一个通用模板便于后期实现新的策略。在这个模板中，有类初始化接口和运行接口，初始化接口最少需要提供账户和市场环境与回测天数。通过编辑运行方法自定义交易逻辑，调用运行方法进行指定天数的策略回测。

```python
class Strategy(object):
    def __init__(self,account:Account,duration:int) -> None:
        pass
    def run(self) -> None:
        pass
```

## 简单网格策略及其实现

### 网格策略

网格交易策略，是一种利用行情震荡进行获利的策略。在标的价格不断震荡的过程中，对标的价格分割出若干上下范围，在市场价格触碰到范围时进行加减仓操作尽可能获利[3]。网格交易策略在投资产品时，首先确定在一定时间范围内该产品的价格的波动范围，把波动范围分割成若干等份，然后根据价格的走势，越跌越买，越涨越卖，实现高抛低吸。该策略使用伪代码描述为：

```fake
m = 总投资额;
r = 投资额中用于初始建仓的的比例;
q = 投资额中用于每次交易的比例;
购入r*m的产品;
对于第i天的产品p_i,循环i{
  根据p_{i-1}和历史价格波动划分网格g;
  如果(p_{i-1}仅突破一次网格线,
    且p_{i-2}与p_i在同一网格范围) {
    不做交易;
  }
  如果(p_i向上突破网格线) {
    买入q*m的产品;
  }
  如果(p_i向下突破网格线) {
    卖出q*m的产品;
  }
}
```

### 参数与变量

`self.grid`将存储给定的网格信息，为交易划分范围限制。`self.batch`存储的是每次网格交易的金额。`self._grid_refers`是字典类型，其中存储当天和前一天的收盘价格，用于与开盘价对比决定当前策略，`self._grid_change`亦是字典类型，记录前一次与前前一次的网格变动情况，如发现变动一次又变回来，则是“假突破”[3]，不进行交易。`self.labels`存储每个网格的编号，并借助`pd.cut`方法[3]实现网格判断。

### 具体实现

部分代码参考了[3]。

```python
class SimpleGridTrade(Strategy):
    def __init__(self,account: Account,
                 grid: list,batch: int,
                 duration: int,establish: dict) -> None:
        self.account = account
        self.grid = np.array(grid)
        self.batch = batch
        self.duration = duration
        self._grid_refers = {}
        self._grid_change = {}
        self.account.establish(establish)
        self.labels = labels = [i for i in range(1,len(self.grid))]
        for k, v in self.account.market._market_data.items():
            self._grid_refers[k] = (0,
                v.closed[self.account.market.today])
            self._grid_change[k] = (0,0)
        self.account.next_day()

    def run(self) -> None:
        for _ in range(self.duration):
            for k, v in self.account.market._market_data.items():
                if self.account.market.today not in v.index:
                    continue
                self._grid_refers[k] = (self._grid_refers[k][-1],
                    v.closed[self.account.market.today] )
                _grid_change_temp = (
                    self._grid_change[k][-1],
                    pd.cut([v.open[self.account.market.today]],self.grid*self._grid_refers[k][0],labels=self.labels)[0]
                ) # 用于后续比较是否为假突破
                if np.isnan(self._grid_change[k][-1]):
                    print(f"{k} out of range at {self.account.market.today}")
                if sorted(_grid_change_temp) == self._grid_change[k]:
                    continue # 假突破 不交易
                else :
                    if _grid_change_temp[-1] == _grid_change_temp[0]:
                        continue
                    elif _grid_change_temp[-1] > _grid_change_temp[0]:
                        self.account.sell(k,self.batch)
                    elif _grid_change_temp[-1] < _grid_change_temp[0]:
                        self.account.buy(k,self.batch)
                self._grid_change[k] = _grid_change_temp
            self.account.next_day()
```

## 回测

本节使用的数据均来自[2]。使用布伦特石油、A股、比特币从2022年4月1日起交易至8月31日，共152自然日（期货股票加密货币一起搞纯纯属于跑着玩，勿喷）。在 Python 3.8.8 IPython 7.22.0 环境下测试。

### 初始化环境与数据

```python
! chcp 65001
# 下载模拟交易代码
! git clone https://gitee.com/jaydencheng/quantitative-trading-simulation.git
! xcopy .\quantitative-trading-simulation\quant_mock .\quant_mock /y /e /i /q
! xcopy .\quantitative-trading-simulation\data .\data /y /e /i /q
! rd /S /Q quantitative-trading-simulation
! dir
```

```python
import quant_mock as qm # 导入模拟交易代码
import pandas as pd
import datetime as dt
```

```python
market_data = {
    'SSEA': pd.read_csv('./data/ssea.csv', index_col='date', parse_dates=True),
    'BTC': pd.read_excel('./data/Bitcoin.xlsx', 'Bitcoin', index_col='date'),
    'Brent': pd.read_excel('./data/Brent.xlsx', 'Brent', index_col='date')
} # 读取数据
```

```python
# 设置参数
TEST_DAYS = 183 # 回测时长
START_DAY = dt.datetime(2022, 3, 1)
CAPITAL = 5000000 # 本金
GRID = [0.97, 0.98, 0.99, 1, 1.01, 1.02, 1.03] # 网格设置
```

```python
# 创建账户与环境
account = qm.Account(market_data,START_DAY, CAPITAL)
```

### 市场数据与可视化

```python
account.market['BTC'].head(3) # 查看比特币市场信息
```

| date       | closed     | open    | high    | low     | volume  |
|-------|------------|---------|---------|---------|---------|
| 2022-01-01 | 47738.0 | 46217.5 | 47917.6 | 46217.5 | 31240.0 |
| 2022-01-02 | 47311.8 | 47738.7 | 47944.9 | 46718.2 | 27020.0 |
| 2022-01-03 | 46430.2 | 47293.9 | 47556.0 | 45704.0 | 41060.0 |

```python
account.market.candle_plot('Brent',START_DAY) # 绘制布伦特蜡烛图
```

<module 'matplotlib.pyplot'>

![png](output_8_1.png)

```python
account.market.volume_plot('SSEA',START_DAY) # 绘制A股交易量
```

<module 'matplotlib.pyplot'>

![png](output_9_1.png)

### 模拟交易

```python
trader = qm.SimpleGridTrade(
    account=account,
    grid=GRID,
    batch=50000,
    duration=TEST_DAYS,
    establish={
        'SSEA': 150000,
        'BTC': 150000,
        'Brent':700000
    }
) # 实例化网格策略交易对象
```

```python
# 回测网格交易
trader.run()
```

### 查看回测效果

```python
account.history
```

|index| date | name       | change | position | price  | balance  | asset      |
|-|------|------------|--------|----------|--------|----------|------------|
| 0    | 2022-03-01 | SSEA   | 41.0     | 41.0   | 3632.27  | 4851076.93 | 5001094.29 |
| 1    | 2022-03-01 | BTC    | 3.0      | 3.0    | 42876.60 | 4722447.13 | 5007165.99 |
| ...  | ...        | ...    | ...      | ...    | ...      | ...        | ...        |
| 220  | 2022-08-31 | Brent  | -505.0   | 8292.0 | 99.00    | 4164369.92 | 5132094.76 |

221 rows × 7 columns

```python
account.revenue_details
```

|date| asset      | rate       | balance  | SSEA       | BTC  | Brent |
|-|------------|------------|----------|------------|------|-------|
| 2022-03-01 | 5073889.76 | 0.014778 | 4022452.83 | 41.0 | 3.0   | 7121.0 |
| 2022-03-02 | 5127858.81 | 0.025572 | 4165210.28 | 28.0 | 2.0   | 6687.0 |
| ...        | ...        | ...      | ...        | ...  | ...   | ...    |
| 2022-08-31 | 5132094.76 | 0.026419 | 4164369.92 | 19.0 | 4.0   | 8292.0 |

184 rows × 6 columns

```python
account.revenue_plot() # 收益率曲线
```

<module 'matplotlib.pyplot''>

![png](output_16_1.png)

```python
account.trade_details_plot('SSEA') # A股交易详情图
```

<module 'matplotlib.pyplot'>

![png](output_17_1.png)

## 需改进的

1. 未考虑到影响较大的手续费；
2. 只能进行整数交易，这对于加密货币是无法忍受的；
3. 假设买入为当日最低值，卖出为当日最高值，显然不现实；
4. 建仓当日为非交易日时会报错；
5. 模拟更多的经典量化交易策略。

## 参考

> [1]廷益--飞鸟. python matplotlib 绘制K线图.[https://blog.csdn.net/weixin_45875105/article/details/107221233]
>
> [2]英为财情. [https://cn.investing.com/]
>
> [3]掘金量化. 网格交易(期货)-经典策略. [https://www.myquant.cn/docs/python_strategyies/104]
