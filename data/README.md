# Data Dictionary

## Main dataset

`比亚迪_后复权日行情_2023-2026.csv`

| Field | Unit | Description |
|---|---|---|
| 日期 | date | Trading date |
| 开盘 / 收盘 / 最高 / 最低 | CNY | Backward-adjusted price (`fqt=2`) |
| 成交量 | hand | One hand = 100 shares |
| 成交额 | CNY | Daily turnover value |
| 振幅 | % | Intraday high-low amplitude |
| 涨跌幅 | % | Daily close-to-close return |
| 涨跌额 | CNY | Daily close-to-close change |
| 换手率 | % | Daily turnover rate |
| MA20 / MA60 / MA120 | CNY | Simple moving averages |
| 运行峰值 | CNY | Running maximum of backward-adjusted close |
| 回撤 | decimal | `close / running_peak - 1` |
| RSI14 | index | Wilder-smoothed RSI |
| MACD_DIF / MACD_DEA / MACD柱 | CNY | MACD components |

## Source files

- `source/比亚迪后复权历史行情数据 (1).xlsx`: user-provided 2023 source.
- `eastmoney_后复权_2023-2026_原始.csv`: API response for overlap checking.
- `年度统计.csv`: annual metrics.
- `月度统计.csv`: monthly metrics.
- `analysis-summary.json`: dashboard summary and methodology metadata.
- `validation.json`: field-level overlap checks.

The API query uses:

```text
secid=0.002594
klt=101
fqt=2
```

`klt=101` means daily data and `fqt=2` means backward-adjusted prices.
