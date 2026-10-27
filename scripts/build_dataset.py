from __future__ import annotations

import json
import math
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SOURCE_DIR = DATA_DIR / "source"
SRC_JSON = DATA_DIR / "dashboard-data.json"
MERGED_CSV = DATA_DIR / "比亚迪_后复权日行情_2023-2026.csv"
API_CSV = DATA_DIR / "eastmoney_后复权_2023-2026_原始.csv"
SUMMARY_JSON = DATA_DIR / "analysis-summary.json"
VALIDATION_JSON = DATA_DIR / "validation.json"

SOURCE_XLSX = SOURCE_DIR / "比亚迪后复权历史行情数据 (1).xlsx"
START_DATE = "20230103"
END_DATE = "20261027"

COLUMNS = [
    "日期",
    "开盘",
    "收盘",
    "最高",
    "最低",
    "成交量",
    "成交额",
    "振幅",
    "涨跌幅",
    "涨跌额",
    "换手率",
]


def as_float(value: object, default: float = 0.0) -> float:
    try:
        number = float(value)
        return number if math.isfinite(number) else default
    except (TypeError, ValueError):
        return default


def load_source() -> pd.DataFrame:
    workbook = openpyxl.load_workbook(SOURCE_XLSX, data_only=True, read_only=True)
    sheet = workbook["Sheet2"]
    rows = list(sheet.iter_rows(values_only=True))
    workbook.close()

    if list(rows[0]) != COLUMNS:
        raise ValueError(f"Unexpected source fields: {rows[0]}")

    frame = pd.DataFrame(rows[1:], columns=COLUMNS)
    frame["日期"] = pd.to_datetime(frame["日期"]).dt.strftime("%Y-%m-%d")
    numeric = COLUMNS[1:]
    frame[numeric] = frame[numeric].apply(pd.to_numeric, errors="coerce")
    frame = frame.dropna(subset=["日期", "开盘", "收盘", "最高", "最低"])
    return frame.sort_values("日期").reset_index(drop=True)


def fetch_eastmoney() -> pd.DataFrame:
    query = urllib.parse.urlencode(
        {
            "secid": "0.002594",
            "klt": "101",
            "fqt": "2",
            "beg": START_DATE,
            "end": END_DATE,
            "lmt": "1000000",
            "iscca": "1",
            "fields1": "f1,f2,f3,f4,f5,f6,f7,f8",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        }
    )
    url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?{query}"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/131 Safari/537.36"
            ),
            "Referer": "https://quote.eastmoney.com/",
        },
    )
    payload = None
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            break
        except Exception as error:  # Network reset is common on quote endpoints.
            last_error = error
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))

    if payload is None:
        if API_CSV.exists():
            print(f"Warning: live fetch failed, using cached API data: {last_error}")
            return pd.read_csv(API_CSV)
        raise RuntimeError(f"Eastmoney fetch failed after retries: {last_error}")

    data = payload.get("data")
    if not data or not data.get("klines"):
        raise RuntimeError("Eastmoney returned no BYD daily K-line data")

    records: list[list[str]] = []
    for row in data["klines"]:
        records.append(row.split(","))

    frame = pd.DataFrame(records, columns=COLUMNS)
    numeric = COLUMNS[1:]
    frame[numeric] = frame[numeric].apply(pd.to_numeric, errors="coerce")
    return frame.sort_values("日期").reset_index(drop=True)


def calculate_indicators(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    close = result["收盘"]

    result["MA20"] = close.rolling(20, min_periods=20).mean().round(3)
    result["MA60"] = close.rolling(60, min_periods=60).mean().round(3)
    result["MA120"] = close.rolling(120, min_periods=120).mean().round(3)

    result["运行峰值"] = close.cummax()
    result["回撤"] = ((close / result["运行峰值"]) - 1).round(6)

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    result["RSI14"] = (100 - (100 / (1 + rs))).round(3)
    result.loc[(avg_loss == 0) & (avg_gain > 0), "RSI14"] = 100

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    result["MACD_DIF"] = (ema12 - ema26).round(4)
    result["MACD_DEA"] = (
        result["MACD_DIF"].ewm(span=9, adjust=False).mean().round(4)
    )
    result["MACD柱"] = ((result["MACD_DIF"] - result["MACD_DEA"]) * 2).round(4)
    return result


def year_summary(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    previous_close: float | None = None
    for year, group in frame.groupby(frame["日期"].str[:4], sort=True):
        group = group.sort_values("日期")
        first = group.iloc[0]
        last = group.iloc[-1]
        start_close = previous_close if previous_close is not None else float(first["收盘"])
        rows.append(
            {
                "年份": year,
                "交易日数": int(len(group)),
                "期初基准": round(start_close, 2),
                "期末收盘": round(float(last["收盘"]), 2),
                "年度涨跌幅": round((float(last["收盘"]) / start_close - 1) * 100, 2),
                "年内最高": round(float(group["最高"].max()), 2),
                "年内最低": round(float(group["最低"].min()), 2),
                "成交额_亿元": round(float(group["成交额"].sum()) / 1e8, 2),
                "日均换手率": round(float(group["换手率"].mean()), 2),
            }
        )
        previous_close = float(last["收盘"])
    return pd.DataFrame(rows)


def monthly_summary(frame: pd.DataFrame) -> pd.DataFrame:
    working = frame.copy()
    working["日期"] = pd.to_datetime(working["日期"])
    monthly = (
        working.set_index("日期")
        .resample("ME")
        .agg(
            {
                "开盘": "first",
                "收盘": "last",
                "最高": "max",
                "最低": "min",
                "成交量": "sum",
                "成交额": "sum",
                "换手率": "mean",
            }
        )
        .dropna()
        .reset_index()
    )
    monthly["月份"] = monthly["日期"].dt.strftime("%Y-%m")
    monthly["月末收盘"] = monthly["收盘"]
    monthly["月度涨跌幅"] = (
        monthly["收盘"].pct_change() * 100
    ).fillna((monthly.iloc[0]["收盘"] / frame.iloc[0]["收盘"] - 1) * 100).round(2)
    monthly["成交额_亿元"] = (monthly["成交额"] / 1e8).round(2)
    monthly["日均换手率"] = monthly["换手率"].round(2)
    return monthly[
        [
            "月份",
            "开盘",
            "最高",
            "最低",
            "月末收盘",
            "月度涨跌幅",
            "成交量",
            "成交额_亿元",
            "日均换手率",
        ]
    ]


def build_summary(
    frame: pd.DataFrame,
    annual: pd.DataFrame,
    validation: dict[str, object],
) -> dict[str, object]:
    close = frame["收盘"].astype(float)
    returns = close.pct_change().dropna()
    drawdown = frame["回撤"].astype(float)
    min_drawdown_index = drawdown.idxmin()
    trough_row = frame.loc[min_drawdown_index]
    peak_rows = frame.loc[:min_drawdown_index]
    peak_row = peak_rows.loc[peak_rows["收盘"].idxmax()]

    high_index = frame["最高"].idxmax()
    low_index = frame["最低"].idxmin()
    latest = frame.iloc[-1]

    first_2023_close = float(frame.iloc[0]["收盘"])
    period_return = (float(latest["收盘"]) / first_2023_close - 1) * 100
    annualized_volatility = float(returns.std(ddof=1) * np.sqrt(252) * 100)
    positive_days = int((returns > 0).sum())
    negative_days = int((returns < 0).sum())

    return {
        "metadata": {
            "stock": "比亚迪",
            "ticker": "002594.SZ",
            "priceBasis": "后复权（fqt=2）",
            "frequency": "日频",
            "startDate": str(frame.iloc[0]["日期"]),
            "endDate": str(latest["日期"]),
            "tradingDays": int(len(frame)),
            "sourceOriginal": "用户提供：比亚迪后复权历史行情数据 (1).xlsx",
            "sourceExtension": (
                "东方财富历史行情接口：secid=0.002594, klt=101, fqt=2"
            ),
            "generatedAtUtc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
        "keyMetrics": {
            "latestClose": round(float(latest["收盘"]), 2),
            "latestDate": str(latest["日期"]),
            "latestChangePct": round(float(latest["涨跌幅"]), 2),
            "periodReturnPct": round(period_return, 2),
            "annualizedVolatilityPct": round(annualized_volatility, 2),
            "maxDrawdownPct": round(float(drawdown.min()) * 100, 2),
            "maxDrawdownPeakDate": str(peak_row["日期"]),
            "maxDrawdownTroughDate": str(trough_row["日期"]),
            "highestPrice": round(float(frame.loc[high_index, "最高"]), 2),
            "highestDate": str(frame.loc[high_index, "日期"]),
            "lowestPrice": round(float(frame.loc[low_index, "最低"]), 2),
            "lowestDate": str(frame.loc[low_index, "日期"]),
            "positiveDays": positive_days,
            "negativeDays": negative_days,
            "winRatePct": round(
                positive_days / (positive_days + negative_days) * 100, 2
            ),
            "latestMA20": round(float(latest["MA20"]), 2),
            "latestMA60": round(float(latest["MA60"]), 2),
            "latestMA120": round(float(latest["MA120"]), 2),
            "latestRSI14": round(float(latest["RSI14"]), 2),
            "latestTurnoverPct": round(float(latest["换手率"]), 2),
        },
        "annualSummary": annual.to_dict(orient="records"),
        "validation": validation,
        "methodology": {
            "return": "收盘价环比收益率",
            "volatility": "日收益率样本标准差 × √252",
            "drawdown": "后复权收盘价相对历史运行峰值的跌幅",
            "ma": "简单移动平均，窗口为 20/60/120 个交易日",
            "rsi": "RSI(14)，Wilder 平滑",
            "annualReturn": "期末收盘 / 上一年末收盘 - 1；2023 年使用首个交易日收盘",
        },
    }


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SOURCE_XLSX.exists():
        raise FileNotFoundError(f"Missing source workbook: {SOURCE_XLSX}")

    original = load_source()
    api = fetch_eastmoney()
    api.to_csv(API_CSV, index=False, encoding="utf-8-sig")

    overlap = original.merge(
        api,
        on="日期",
        suffixes=("_原表", "_接口"),
        how="inner",
    )
    if len(overlap) != len(original):
        raise ValueError(
            f"2023 overlap mismatch: original={len(original)}, overlap={len(overlap)}"
        )

    comparisons: dict[str, float] = {}
    for column in COLUMNS[1:]:
        diff = (overlap[f"{column}_原表"] - overlap[f"{column}_接口"]).abs()
        comparisons[column] = round(float(diff.max()), 4)

    validation = {
        "overlapRows": int(len(overlap)),
        "originalRows": int(len(original)),
        "maxAbsDifferenceByField": comparisons,
        "sameTradingCalendar": bool(
            original["日期"].tolist() == overlap["日期"].tolist()
        ),
        "adjustmentMatched": bool(
            comparisons["开盘"] < 0.01
            and comparisons["收盘"] < 0.01
            and comparisons["最高"] < 0.01
            and comparisons["最低"] < 0.01
        ),
    }
    VALIDATION_JSON.write_text(
        json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    extension = api[api["日期"] > original["日期"].max()].copy()
    merged = pd.concat([original, extension], ignore_index=True)
    merged = merged.drop_duplicates("日期", keep="first").sort_values("日期")
    merged = merged.reset_index(drop=True)
    merged = calculate_indicators(merged)

    annual = year_summary(merged)
    monthly = monthly_summary(merged)
    summary = build_summary(merged, annual, validation)

    merged.to_csv(MERGED_CSV, index=False, encoding="utf-8-sig")
    annual.to_csv(DATA_DIR / "年度统计.csv", index=False, encoding="utf-8-sig")
    monthly.to_csv(DATA_DIR / "月度统计.csv", index=False, encoding="utf-8-sig")
    SUMMARY_JSON.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    records: list[dict[str, object]] = []
    for _, row in merged.iterrows():
        record: dict[str, object] = {}
        for key, value in row.items():
            if pd.isna(value):
                record[key] = None
            elif isinstance(value, (np.integer,)):
                record[key] = int(value)
            elif isinstance(value, (np.floating,)):
                record[key] = round(float(value), 4)
            else:
                record[key] = value
        records.append(record)

    web_data = {
        "summary": summary,
        "records": records,
        "monthly": monthly.to_dict(orient="records"),
    }
    SRC_JSON.write_text(
        json.dumps(web_data, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "rows": len(merged),
                "range": [merged.iloc[0]["日期"], merged.iloc[-1]["日期"]],
                "adjustmentMatched": validation["adjustmentMatched"],
                "latestClose": summary["keyMetrics"]["latestClose"],
                "periodReturnPct": summary["keyMetrics"]["periodReturnPct"],
                "maxDrawdownPct": summary["keyMetrics"]["maxDrawdownPct"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
