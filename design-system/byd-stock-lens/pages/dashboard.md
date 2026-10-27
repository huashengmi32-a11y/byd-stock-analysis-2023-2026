# Dashboard Page Override

This page overrides the generated Master where the two conflict.

## Decision

Use a paper-white analytical workspace instead of the generated OLED dark-mode
landing-page pattern. The audience is a student and instructor reviewing a
financial time series in daylight, often comparing values and exporting data.
A light, low-saturation canvas improves table legibility and keeps the red/green
market semantics dominant.

The generated "Enterprise Gateway" section order and sales CTAs do not apply.
This is a working analysis dashboard, not a marketing page.

## Visual tokens

| Role | Value | Use |
|---|---|---|
| Canvas | `#F3F4EF` | Page background |
| Surface | `#FCFCF8` | Chart and table surfaces |
| Ink | `#17212B` | Primary text and controls |
| Muted ink | `#65717C` | Supporting labels |
| Hairline | `#D9DDD6` | Grid lines and borders |
| Market up | `#C73A42` | Positive return in China-market convention |
| Market down | `#15805D` | Negative return in China-market convention |
| Analysis blue | `#2E5C8A` | Neutral trend and MA20 |
| Amber | `#A8752A` | MA60 and warnings |

Use color with signs, candle fill, labels, or line styles. Never communicate
positive or negative returns through color alone.

## Layout

- 64 px top bar, full width, no floating marketing hero.
- A title-and-price band immediately followed by time-range controls.
- Six compact KPI cells on desktop; two columns on mobile.
- Main chart (two-thirds width) and annual-performance panel (one-third).
- Secondary row for monthly-return and risk-context panels.
- Data table below charts with an accessible horizontal-scroll wrapper.
- Maximum content width 1560 px, 20 px mobile gutters.
- Card radius 8 px maximum. Use borders more than shadows.

## Typography

- Chinese UI: `"Microsoft YaHei", "Noto Sans SC", sans-serif`.
- Numeric display: `"Cascadia Mono", "IBM Plex Mono", monospace`.
- Body text at least 14 px desktop and 16 px mobile.
- Tabular numbers for prices, returns, and tabular data.
- Letter spacing stays at `0`.

## Controls

- TDesign Vue Next: RadioGroup, DateRangePicker, Select, Switch, Tabs, Button,
  Tag, Tooltip, Table, and Pagination.
- Minimum 44 px touch target for controls.
- Visible 2 px focus ring with 2 px offset.
- Use TDesign icons from `tdesign-icons-vue-next`; no emoji or hand-drawn UI icons.
- Tooltips label unfamiliar icons and explain financial ratios.

## Chart behavior

- ECharts Canvas for K-line, volume, moving averages, drawdown, and monthly bars.
- Default chart shows candlesticks plus volume, with MAs available via a switch.
- Up candles are red and down candles are green; no hollow/filled reliance alone.
- Data points expose exact OHLC values in a tooltip.
- A visible OHLC fallback exists in the table at every viewport.
- Controls must preserve a stable chart height to avoid layout shift.

## Motion

Use 160-220 ms state transitions only. Respect `prefers-reduced-motion`.
No autoplay, looping animation, or scroll-triggered chart reveals.

## Pre-delivery checks

- No horizontal page scroll at 320/375/414/768/1024/1440 px.
- Canvas nonblank and red/green pixels present.
- Keyboard reaches every control in reading order.
- No text overlap at 200% zoom.
- CSV export matches the visible selected range.
- Source range and adjustment basis appear in the page and workbook.
