# BYD Stock Analysis Project Guide

## Project purpose

This repository completes the textbook P92 stock-price analysis exercise for BYD
(`002594.SZ`) using daily forward-adjusted (`fqt=2`, 后复权) market data from
2023-01-03 through the latest trading day on or before 2026-10-27.

The deliverable has two equally important surfaces:

1. An Excel workbook for the course submission and source-data review.
2. A responsive web dashboard built with Vue 3, TDesign Vue Next, and ECharts.

## Commands

```powershell
# Rebuild the merged dataset and analysis metrics
python scripts/build_dataset.py

# Build the formatted Excel workbook
python scripts/build_workbook.py

# Install and run the dashboard
pnpm install
pnpm dev

# Production build and verification
pnpm build
pnpm verify
```

## Data rules

- Keep the original 2023 rows exactly as supplied by the user.
- Merge public market data only after a field-by-field overlap check.
- Use Eastmoney `secid=0.002594`, `klt=101`, and `fqt=2` for the extension.
- Never mix unadjusted, forward-adjusted, and backward-adjusted prices.
- Volume is in hands (手); turnover is in CNY.
- Treat "2026" as year-to-date through the last available trading date. Do not
  invent future dates or interpolate market holidays.

## UI rules

- Use TDesign Vue Next controls for interactive controls and data tables.
- Use ECharts for financial charts; the chart library is not a UI-control substitute.
- China-market convention: red means price up, green means price down. Pair color
  with signed text or candle fill so the meaning is never color-only.
- Keep the dashboard workspace-like and information-dense. No landing-page hero.
- Support keyboard focus, visible focus rings, 44 px touch targets, reduced motion,
  and responsive layouts from 320 px upward.
- Follow `design-system/byd-stock-lens/MASTER.md` as the visual source of truth.

## Financial analysis rules

- Use close-to-close returns and 252 trading days for annualized volatility.
- Calculate maximum drawdown from the running peak of backward-adjusted close.
- MA(20), MA(60), and MA(120) use closing prices.
- RSI(14) uses Wilder smoothing.
- Annual return uses the year-end close versus the previous year-end close; 2023
  uses its first trading-day close as the starting baseline.
- State that indicators are descriptive statistics, not investment advice.

## Verification

- Run `python scripts/validate_data.py` after rebuilding data.
- Run `pnpm verify` before publishing.
- Confirm the dashboard has no console errors, no blank canvases, and no text or
  chart overlap at 375 px, 768 px, 1024 px, and 1440 px.
- Keep `docs/对话流.md` synchronized with the final scope, decisions, rejected
  alternatives, validation results, and final data evidence.
