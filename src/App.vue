<script setup>
import { computed, ref, watch } from "vue";
import {
  CalendarIcon,
  ChartIcon,
  DownloadIcon,
  InfoCircleFilledIcon,
  RefreshIcon,
} from "tdesign-icons-vue-next";
import EChart from "./components/EChart.vue";
import stockData from "../data/dashboard-data.json";

const records = stockData.records;
const summary = stockData.summary;
const months = stockData.monthly;
const firstDate = records[0]["日期"];
const lastDate = records.at(-1)["日期"];

const selectedPeriod = ref("all");
const dateRange = ref([firstDate, lastDate]);
const chartMode = ref("kline");
const showMA = ref(true);
const maPreset = ref("all");
const currentPage = ref(1);
const pageSize = ref(10);

const periodOptions = [
  { label: "1 月", value: "1m" },
  { label: "3 月", value: "3m" },
  { label: "6 月", value: "6m" },
  { label: "1 年", value: "1y" },
  { label: "3 年", value: "3y" },
  { label: "全周期", value: "all" },
];

const maOptions = [
  { label: "MA20 + MA60 + MA120", value: "all" },
  { label: "MA20 + MA60", value: "20-60" },
  { label: "仅 MA20", value: "20" },
  { label: "不叠加均线", value: "none" },
];

const chartModeOptions = [
  { label: "K 线", value: "kline" },
  { label: "均线趋势", value: "line" },
  { label: "回撤", value: "drawdown" },
  { label: "月度收益", value: "monthly" },
];

const tableColumns = [
  { colKey: "日期", title: "日期", width: 118, fixed: "left" },
  { colKey: "开盘", title: "开盘", align: "right", width: 92 },
  { colKey: "收盘", title: "收盘", align: "right", width: 92 },
  { colKey: "最高", title: "最高", align: "right", width: 92 },
  { colKey: "最低", title: "最低", align: "right", width: 92 },
  {
    colKey: "涨跌幅",
    title: "涨跌幅",
    cell: "changeCell",
    align: "right",
    width: 104,
  },
  {
    colKey: "成交量",
    title: "成交量(万手)",
    cell: "volumeCell",
    align: "right",
    width: 132,
  },
  {
    colKey: "成交额",
    title: "成交额(亿)",
    cell: "amountCell",
    align: "right",
    width: 124,
  },
  {
    colKey: "换手率",
    title: "换手率",
    cell: "turnoverCell",
    align: "right",
    width: 96,
  },
];

function toDate(value) {
  return new Date(`${value}T00:00:00+08:00`);
}

function dateString(value) {
  if (typeof value === "string") return value.slice(0, 10);
  const date = new Date(value);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function shiftDate(value, days) {
  const date = toDate(value);
  date.setDate(date.getDate() - days);
  return dateString(date);
}

function applyPeriod(value) {
  selectedPeriod.value = value;
  const days = {
    "1m": 31,
    "3m": 93,
    "6m": 186,
    "1y": 366,
    "3y": 1098,
  }[value];
  dateRange.value = days
    ? [shiftDate(lastDate, days), lastDate]
    : [firstDate, lastDate];
}

function onCustomRange(value) {
  if (!Array.isArray(value) || value.length !== 2) return;
  const normalized = value.map(dateString).sort();
  const minDate = normalized[0] < firstDate ? firstDate : normalized[0];
  const maxDate = normalized[1] > lastDate ? lastDate : normalized[1];
  dateRange.value = [minDate, maxDate];
  selectedPeriod.value = "custom";
}

function resetRange() {
  selectedPeriod.value = "all";
  dateRange.value = [firstDate, lastDate];
}

const filtered = computed(() => {
  const [start, end] = dateRange.value;
  return records.filter((row) => row["日期"] >= start && row["日期"] <= end);
});

watch(filtered, () => {
  currentPage.value = 1;
});

const metrics = computed(() => {
  const rows = filtered.value;
  if (!rows.length) {
    return {
      periodReturn: 0,
      volatility: 0,
      drawdown: 0,
      peakDate: "--",
      troughDate: "--",
      high: 0,
      highDate: "--",
      low: 0,
      lowDate: "--",
      avgTurnover: 0,
      winRate: 0,
      positiveDays: 0,
      negativeDays: 0,
      latestClose: records.at(-1)["收盘"],
      latestChange: records.at(-1)["涨跌幅"],
    };
  }

  const firstClose = rows[0]["收盘"];
  const last = rows.at(-1);
  const dailyReturns = [];
  for (let index = 1; index < rows.length; index += 1) {
    dailyReturns.push(rows[index]["收盘"] / rows[index - 1]["收盘"] - 1);
  }
  const mean =
    dailyReturns.reduce((total, value) => total + value, 0) /
    Math.max(dailyReturns.length, 1);
  const variance =
    dailyReturns.reduce((total, value) => total + (value - mean) ** 2, 0) /
    Math.max(dailyReturns.length - 1, 1);
  const volatility = Math.sqrt(variance) * Math.sqrt(252) * 100;

  let runningPeak = -Infinity;
  let peakDate = rows[0]["日期"];
  let maxDrawdown = 0;
  let maxPeakDate = rows[0]["日期"];
  let maxTroughDate = rows[0]["日期"];
  rows.forEach((row) => {
    if (row["收盘"] > runningPeak) {
      runningPeak = row["收盘"];
      peakDate = row["日期"];
    }
    const drawdown = row["收盘"] / runningPeak - 1;
    if (drawdown < maxDrawdown) {
      maxDrawdown = drawdown;
      maxPeakDate = peakDate;
      maxTroughDate = row["日期"];
    }
  });

  const highRow = rows.reduce((best, row) =>
    row["最高"] > best["最高"] ? row : best,
  );
  const lowRow = rows.reduce((best, row) =>
    row["最低"] < best["最低"] ? row : best,
  );
  const positiveDays = dailyReturns.filter((value) => value > 0).length;
  const negativeDays = dailyReturns.filter((value) => value < 0).length;
  const directionDays = positiveDays + negativeDays;

  return {
    periodReturn: (last["收盘"] / firstClose - 1) * 100,
    volatility,
    drawdown: maxDrawdown * 100,
    peakDate: maxPeakDate,
    troughDate: maxTroughDate,
    high: highRow["最高"],
    highDate: highRow["日期"],
    low: lowRow["最低"],
    lowDate: lowRow["日期"],
    avgTurnover:
      rows.reduce((total, row) => total + row["换手率"], 0) / rows.length,
    winRate: directionDays ? (positiveDays / directionDays) * 100 : 0,
    positiveDays,
    negativeDays,
    latestClose: last["收盘"],
    latestChange: last["涨跌幅"],
  };
});

const rangeLabel = computed(
  () => `${filtered.value[0]?.["日期"] || "--"} — ${filtered.value.at(-1)?.["日期"] || "--"}`,
);

const latestRecord = records.at(-1);
const latestUp = latestRecord["涨跌幅"] >= 0;

const metricCards = computed(() => [
  {
    label: "区间涨跌",
    value: `${signed(metrics.value.periodReturn)}%`,
    tone:
      metrics.value.periodReturn > 0
        ? "up"
        : metrics.value.periodReturn < 0
          ? "down"
          : "flat",
    note: `${filtered.value.length} 个交易日`,
    help: "所选区间最后收盘价相对首个收盘价的涨跌幅。",
  },
  {
    label: "年化波动率",
    value: `${metrics.value.volatility.toFixed(1)}%`,
    tone: "neutral",
    note: "252 日年化",
    help: "日收益率样本标准差乘以 √252，衡量价格波动，不代表风险全部。",
  },
  {
    label: "最大回撤",
    value: `${metrics.value.drawdown.toFixed(2)}%`,
    tone: "down",
    note: `${metrics.value.peakDate} → ${metrics.value.troughDate}`,
    help: "收盘价相对此前运行峰值的最大跌幅；负值越大，历史回撤越深。",
  },
  {
    label: "区间最高",
    value: `${metrics.value.high.toFixed(2)}`,
    tone: "up",
    note: metrics.value.highDate,
  },
  {
    label: "区间最低",
    value: `${metrics.value.low.toFixed(2)}`,
    tone: "down",
    note: metrics.value.lowDate,
  },
  {
    label: "日均换手率",
    value: `${metrics.value.avgTurnover.toFixed(2)}%`,
    tone: "neutral",
    note: "区间算术平均",
  },
]);

function signed(value, digits = 2) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "0.00";
  return `${number > 0 ? "+" : ""}${number.toFixed(digits)}`;
}

function formatNumber(value, digits = 2) {
  return Number(value).toLocaleString("zh-CN", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function formatDateShort(value) {
  return String(value).slice(2).replaceAll("-", "/");
}

const axisStyle = {
  axisLine: { lineStyle: { color: "#AEB5AE" } },
  axisTick: { show: false },
  axisLabel: { color: "#65717C", fontSize: 11 },
  splitLine: { lineStyle: { color: "#E5E7E1", type: "dashed" } },
};

const tooltipStyle = {
  backgroundColor: "rgba(23, 33, 43, 0.96)",
  borderWidth: 0,
  textStyle: { color: "#F8F8F3", fontSize: 12 },
  extraCssText: "box-shadow:0 8px 24px rgba(23,33,43,.18);border-radius:6px;",
};

function maSeries(rows, categories) {
  const keys =
    maPreset.value === "none" || !showMA.value
      ? []
      : maPreset.value === "20"
        ? [20]
        : maPreset.value === "20-60"
          ? [20, 60]
          : [20, 60, 120];
  return keys.map((period) => ({
    name: `MA${period}`,
    type: "line",
    data: rows.map((row) => row[`MA${period}`]),
    symbol: "none",
    smooth: true,
    connectNulls: false,
    lineStyle: {
      width: period === 20 ? 1.7 : 1.3,
      type: period === 120 ? "dashed" : "solid",
    },
    itemStyle: {
      color: period === 20 ? "#2E5C8A" : period === 60 ? "#A8752A" : "#7C5D9E",
    },
    emphasis: { disabled: true },
    z: 4,
  }));
}

const priceChartOption = computed(() => {
  const rows = filtered.value;
  const categories = rows.map((row) => row["日期"]);
  const ma = maSeries(rows, categories);
  const volumeData = rows.map((row) => ({
    value: row["成交量"] / 10000,
    itemStyle: {
      color: row["收盘"] >= row["开盘"] ? "#C73A42AA" : "#15805DAA",
    },
  }));

  if (chartMode.value === "monthly") {
    const visibleMonths = months.filter(
      (month) =>
        month["月份"] >= categories[0]?.slice(0, 7) &&
        month["月份"] <= categories.at(-1)?.slice(0, 7),
    );
    return {
      animationDuration: 220,
      animationDurationUpdate: 180,
      aria: {
        enabled: true,
        decal: { show: false },
        description: "所选区间的月度涨跌幅柱状图，红色为正，绿色为负。",
      },
      tooltip: {
        ...tooltipStyle,
        trigger: "axis",
        axisPointer: { type: "shadow" },
        formatter: (params) => {
          const row = visibleMonths[params[0].dataIndex];
          return [
            `<strong>${row["月份"]}</strong>`,
            `月度涨跌：<span style="color:${row["月度涨跌幅"] >= 0 ? "#FF8B90" : "#77C9AE"}">${signed(row["月度涨跌幅"])}%</span>`,
            `月末收盘：${formatNumber(row["月末收盘"])} 元`,
            `成交额：${formatNumber(row["成交额_亿元"])} 亿元`,
          ].join("<br/>");
        },
      },
      grid: { left: 58, right: 22, top: 32, bottom: 56 },
      xAxis: {
        type: "category",
        data: visibleMonths.map((row) => row["月份"]),
        ...axisStyle,
        axisLabel: { color: "#65717C", fontSize: 10, rotate: 35 },
      },
      yAxis: {
        type: "value",
        name: "月度收益 %",
        nameTextStyle: { color: "#65717C", align: "left" },
        ...axisStyle,
      },
      dataZoom: [{ type: "inside", start: 0, end: 100 }],
      series: [
        {
          name: "月度涨跌幅",
          type: "bar",
          barMaxWidth: 22,
          data: visibleMonths.map((row) => ({
            value: row["月度涨跌幅"],
            itemStyle: {
              color: row["月度涨跌幅"] >= 0 ? "#C73A42" : "#15805D",
            },
            label: {
              show: visibleMonths.length <= 12,
              position: row["月度涨跌幅"] >= 0 ? "top" : "bottom",
              color: "#48545E",
              fontSize: 10,
              formatter: `${signed(row["月度涨跌幅"], 1)}%`,
            },
          })),
          markLine: {
            silent: true,
            symbol: "none",
            lineStyle: { color: "#9DA69E", type: "dashed" },
            label: { show: false },
            data: [{ yAxis: 0 }],
          },
        },
      ],
    };
  }

  if (chartMode.value === "drawdown") {
    return {
      animationDuration: 220,
      animationDurationUpdate: 180,
      aria: {
        enabled: true,
        description: "所选区间的后复权收盘价回撤曲线。",
      },
      tooltip: {
        ...tooltipStyle,
        trigger: "axis",
        axisPointer: { type: "line" },
        formatter: (params) => {
          const row = rows[params[0].dataIndex];
          return [
            `<strong>${row["日期"]}</strong>`,
            `收盘：${formatNumber(row["收盘"])} 元`,
            `回撤：${signed(row["回撤"] * 100)}%`,
            `运行峰值：${formatNumber(row["运行峰值"])} 元`,
          ].join("<br/>");
        },
      },
      grid: { left: 64, right: 24, top: 38, bottom: 64 },
      xAxis: {
        type: "category",
        data: categories,
        ...axisStyle,
        axisLabel: {
          color: "#65717C",
          fontSize: 10,
          formatter: formatDateShort,
        },
      },
      yAxis: {
        type: "value",
        max: 0,
        axisLabel: { formatter: "{value}%", color: "#65717C", fontSize: 11 },
        ...axisStyle,
      },
      dataZoom: [
        { type: "inside", start: 0, end: 100 },
        {
          type: "slider",
          height: 18,
          bottom: 12,
          borderColor: "transparent",
          backgroundColor: "#EBEDE7",
          fillerColor: "#C73A4230",
          handleStyle: { color: "#17212B" },
        },
      ],
      series: [
        {
          name: "回撤",
          type: "line",
          data: rows.map((row) => Number((row["回撤"] * 100).toFixed(3))),
          symbol: "none",
          lineStyle: { width: 1.6, color: "#C73A42" },
          areaStyle: {
            color: {
              type: "linear",
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: "rgba(199,58,66,0.08)" },
                { offset: 1, color: "rgba(199,58,66,0.34)" },
              ],
            },
          },
        },
      ],
    };
  }

  if (chartMode.value === "line") {
    return {
      animationDuration: 220,
      animationDurationUpdate: 180,
      aria: {
        enabled: true,
        description: "所选区间的后复权收盘价及移动平均线。",
      },
      tooltip: {
        ...tooltipStyle,
        trigger: "axis",
        axisPointer: { type: "line" },
        formatter: (params) => {
          const row = rows[params[0].dataIndex];
          const selected = params
            .filter((item) => item.seriesName !== "成交量")
            .map(
              (item) =>
                `${item.marker}${item.seriesName}：${formatNumber(item.value)}`,
            )
            .join("<br/>");
          return [`<strong>${row["日期"]}</strong>`, selected].join("<br/>");
        },
      },
      grid: { left: 62, right: 22, top: 34, bottom: 66 },
      xAxis: {
        type: "category",
        data: categories,
        boundaryGap: false,
        ...axisStyle,
        axisLabel: {
          color: "#65717C",
          fontSize: 10,
          formatter: formatDateShort,
        },
      },
      yAxis: {
        type: "value",
        name: "后复权价 / 元",
        scale: true,
        nameTextStyle: { color: "#65717C", align: "left" },
        ...axisStyle,
      },
      dataZoom: [
        { type: "inside", start: 0, end: 100 },
        {
          type: "slider",
          height: 18,
          bottom: 12,
          borderColor: "transparent",
          backgroundColor: "#EBEDE7",
          fillerColor: "#2E5C8A25",
          handleStyle: { color: "#17212B" },
        },
      ],
      series: [
        {
          name: "收盘",
          type: "line",
          data: rows.map((row) => row["收盘"]),
          symbol: "none",
          lineStyle: { width: 2, color: "#17212B" },
          areaStyle: {
            color: {
              type: "linear",
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: "rgba(46,92,138,0.18)" },
                { offset: 1, color: "rgba(46,92,138,0.01)" },
              ],
            },
          },
          markPoint: {
            symbol: "circle",
            symbolSize: 7,
            data: [
              {
                type: "max",
                name: "区间最高",
                itemStyle: { color: "#C73A42" },
                label: {
                  formatter: "高 {c}",
                  color: "#C73A42",
                  position: "top",
                  fontSize: 10,
                },
              },
              {
                type: "min",
                name: "区间最低",
                itemStyle: { color: "#15805D" },
                label: {
                  formatter: "低 {c}",
                  color: "#15805D",
                  position: "bottom",
                  fontSize: 10,
                },
              },
            ],
          },
        },
        ...ma,
      ],
    };
  }

  return {
    animationDuration: 220,
    animationDurationUpdate: 180,
    aria: {
      enabled: true,
      description:
        "所选区间的比亚迪后复权日K线及成交量，红色上涨，绿色下跌。",
    },
    tooltip: {
      ...tooltipStyle,
      trigger: "axis",
      axisPointer: { type: "cross", lineStyle: { color: "#87918A" } },
      formatter: (params) => {
        const candle = params.find((item) => item.seriesType === "candlestick");
        if (!candle) return "";
        const row = rows[candle.dataIndex];
        const volume = params.find((item) => item.seriesName === "成交量");
        return [
          `<strong>${row["日期"]}</strong>`,
          `开盘 ${formatNumber(row["开盘"])}　收盘 ${formatNumber(row["收盘"])}`,
          `最高 ${formatNumber(row["最高"])}　最低 ${formatNumber(row["最低"])}`,
          `涨跌幅 <span style="color:${row["涨跌幅"] >= 0 ? "#FF8B90" : "#77C9AE"}">${signed(row["涨跌幅"])}%</span>`,
          `成交量 ${volume ? formatNumber(volume.value) : formatNumber(row["成交量"] / 10000)} 万手`,
          `换手率 ${formatNumber(row["换手率"])}%`,
        ].join("<br/>");
      },
    },
    axisPointer: {
      link: [{ xAxisIndex: "all" }],
      label: { backgroundColor: "#17212B" },
    },
    grid: [
      { left: 62, right: 22, top: 34, height: "60%" },
      { left: 62, right: 22, top: "74%", height: "12%" },
    ],
    xAxis: [
      {
        type: "category",
        data: categories,
        boundaryGap: true,
        ...axisStyle,
        axisLabel: { show: false },
      },
      {
        type: "category",
        gridIndex: 1,
        data: categories,
        boundaryGap: true,
        ...axisStyle,
        axisLabel: {
          color: "#65717C",
          fontSize: 10,
          formatter: formatDateShort,
        },
      },
    ],
    yAxis: [
      {
        type: "value",
        scale: true,
        name: "后复权价 / 元",
        nameTextStyle: { color: "#65717C", align: "left" },
        ...axisStyle,
      },
      {
        type: "value",
        scale: true,
        gridIndex: 1,
        name: "万手",
        nameTextStyle: { color: "#65717C", align: "left", fontSize: 10 },
        axisLabel: { color: "#65717C", fontSize: 10 },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
      },
    ],
    dataZoom: [
      { type: "inside", xAxisIndex: [0, 1], start: 0, end: 100 },
      {
        type: "slider",
        xAxisIndex: [0, 1],
        height: 18,
        bottom: 8,
        borderColor: "transparent",
        backgroundColor: "#EBEDE7",
        fillerColor: "#17212B18",
        handleStyle: { color: "#17212B" },
        textStyle: { color: "#65717C", fontSize: 9 },
      },
    ],
    series: [
      {
        name: "价格",
        type: "candlestick",
        data: rows.map((row) => [
          row["开盘"],
          row["收盘"],
          row["最低"],
          row["最高"],
        ]),
        itemStyle: {
          color: "#C73A42",
          color0: "#15805D",
          borderColor: "#C73A42",
          borderColor0: "#15805D",
          borderWidth: 1,
        },
        emphasis: {
          itemStyle: {
            color: "#E85A62",
            color0: "#1A9B70",
            borderColor: "#E85A62",
            borderColor0: "#1A9B70",
          },
        },
        z: 3,
      },
      ...ma,
      {
        name: "成交量",
        type: "bar",
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumeData,
        barMaxWidth: 8,
      },
    ],
  };
});

const annualChartOption = computed(() => {
  const rows = summary.annualSummary;
  return {
    animationDuration: 220,
    aria: {
      enabled: true,
      description: "2023 至 2026 年年度涨跌幅，红色上涨，绿色下跌。",
    },
    tooltip: {
      ...tooltipStyle,
      trigger: "axis",
      axisPointer: { type: "shadow" },
      formatter: (params) => {
        const row = rows[params[0].dataIndex];
        return [
          `<strong>${row["年份"]}</strong>`,
          `年度涨跌：${signed(row["年度涨跌幅"])}%`,
          `期末收盘：${formatNumber(row["期末收盘"])}`,
          `成交额：${formatNumber(row["成交额_亿元"])} 亿元`,
        ].join("<br/>");
      },
    },
    grid: { left: 42, right: 12, top: 22, bottom: 32 },
    xAxis: {
      type: "category",
      data: rows.map((row) => row["年份"]),
      ...axisStyle,
      splitLine: { show: false },
    },
    yAxis: {
      type: "value",
      axisLabel: { formatter: "{value}%", color: "#65717C", fontSize: 10 },
      ...axisStyle,
    },
    series: [
      {
        name: "年度涨跌幅",
        type: "bar",
        barMaxWidth: 38,
        data: rows.map((row) => ({
          value: row["年度涨跌幅"],
          itemStyle: {
            color: row["年度涨跌幅"] >= 0 ? "#C73A42" : "#15805D",
            borderRadius: 2,
          },
          label: {
            show: true,
            position: row["年度涨跌幅"] >= 0 ? "top" : "bottom",
            color: "#48545E",
            fontSize: 10,
            formatter: `${signed(row["年度涨跌幅"], 1)}%`,
          },
        })),
        markLine: {
          silent: true,
          symbol: "none",
          lineStyle: { color: "#AAB2AB", type: "dashed" },
          label: { show: false },
          data: [{ yAxis: 0 }],
        },
      },
    ],
  };
});

const monthlyChartOption = computed(() => {
  const visibleMonths = months.filter(
    (month) =>
      month["月份"] >= dateRange.value[0].slice(0, 7) &&
      month["月份"] <= dateRange.value[1].slice(0, 7),
  );
  return {
    animationDuration: 180,
    aria: {
      enabled: true,
      description: "所选区间的月度成交额和月度涨跌幅。",
    },
    tooltip: {
      ...tooltipStyle,
      trigger: "axis",
      formatter: (params) => {
        const row = visibleMonths[params[0].dataIndex];
        return [
          `<strong>${row["月份"]}</strong>`,
          `成交额：${formatNumber(row["成交额_亿元"])} 亿元`,
          `月度涨跌：${signed(row["月度涨跌幅"])}%`,
          `日均换手：${formatNumber(row["日均换手率"])}%`,
        ].join("<br/>");
      },
    },
    grid: { left: 48, right: 16, top: 26, bottom: 36 },
    xAxis: {
      type: "category",
      data: visibleMonths.map((row) => row["月份"].slice(2)),
      ...axisStyle,
      axisLabel: { color: "#65717C", fontSize: 9, rotate: 40 },
    },
    yAxis: [
      {
        type: "value",
        name: "亿元",
        nameTextStyle: { color: "#65717C", fontSize: 10 },
        ...axisStyle,
      },
      {
        type: "value",
        name: "%",
        nameTextStyle: { color: "#A8752A", fontSize: 10 },
        axisLabel: { formatter: "{value}%", color: "#A8752A", fontSize: 10 },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
      },
    ],
    dataZoom: [{ type: "inside", start: 0, end: 100 }],
    series: [
      {
        name: "成交额",
        type: "bar",
        barMaxWidth: 18,
        data: visibleMonths.map((row) => ({
          value: row["成交额_亿元"],
          itemStyle: {
            color: row["月度涨跌幅"] >= 0 ? "#C73A42" : "#15805D",
          },
        })),
      },
      {
        name: "月度涨跌",
        type: "line",
        yAxisIndex: 1,
        data: visibleMonths.map((row) => row["月度涨跌幅"]),
        symbol: "none",
        lineStyle: { color: "#A8752A", width: 1.4, type: "dashed" },
        tooltip: { show: false },
        z: 4,
      },
    ],
  };
});

const riskFacts = computed(() => [
  { label: "日胜率", value: `${metrics.value.winRate.toFixed(1)}%` },
  {
    label: "上涨 / 下跌日",
    value: `${metrics.value.positiveDays} / ${metrics.value.negativeDays}`,
  },
  {
    label: "回撤区间",
    value: `${metrics.value.peakDate} → ${metrics.value.troughDate}`,
  },
  {
    label: "最新均线",
    value: `MA20 ${formatNumber(filtered.value.at(-1)?.["MA20"] || 0)}`,
  },
]);

const insightItems = computed(() => {
  const last = filtered.value.at(-1);
  const ma20 = last?.["MA20"];
  const trend =
    last && ma20
      ? last["收盘"] >= ma20
        ? `区间末收盘价高于 MA20，短线趋势相对偏强；但仍需结合更长周期确认。`
        : `区间末收盘价低于 MA20，短线仍处于均线下方，趋势尚未完成修复。`
      : "当前区间不足以形成稳定的均线判断。";
  const annualBest = [...summary.annualSummary].sort(
    (a, b) => b["年度涨跌幅"] - a["年度涨跌幅"],
  )[0];
  const annualWorst = [...summary.annualSummary].sort(
    (a, b) => a["年度涨跌幅"] - b["年度涨跌幅"],
  )[0];
  return [
    trend,
    `最大回撤为 ${metrics.value.drawdown.toFixed(2)}%，发生在 ${metrics.value.peakDate} 至 ${metrics.value.troughDate}，说明趋势交易必须重视下行风险。`,
    `${annualBest["年份"]} 年表现最强（${signed(annualBest["年度涨跌幅"])}%），${annualWorst["年份"]} 年表现最弱（${signed(annualWorst["年度涨跌幅"])}%）。`,
  ];
});

const sortedRows = computed(
  () =>
    [...filtered.value]
      .reverse()
      .map((row) => ({
        ...row,
        成交量: row["成交量"] / 10000,
        成交额: row["成交额"] / 1e8,
      })),
);

const pagedRows = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return sortedRows.value.slice(start, start + pageSize.value);
});

function onPageChange(pageInfo) {
  currentPage.value = pageInfo.current;
}

function onPageSizeChange(size) {
  pageSize.value = size;
  currentPage.value = 1;
}

function exportCsv() {
  const headers = [
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
    "MA20",
    "MA60",
    "MA120",
    "回撤",
  ];
  const rows = filtered.value.map((row) =>
    headers
      .map((header) => {
        const value = row[header];
        return value === null || value === undefined ? "" : value;
      })
      .join(","),
  );
  const content = `\uFEFF${headers.join(",")}\n${rows.join("\n")}`;
  const blob = new Blob([content], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  const startDate = filtered.value[0]?.["日期"] || dateRange.value[0];
  const endDate = filtered.value.at(-1)?.["日期"] || dateRange.value[1];
  link.href = url;
  link.download = `比亚迪_${startDate}_${endDate}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <a class="brand" href="#overview" aria-label="回到页面顶部">
        <span class="brand-mark"><ChartIcon size="20px" /></span>
        <span>
          <strong>BYD Lens</strong>
          <small>股票走势分析</small>
        </span>
      </a>
      <nav class="topnav" aria-label="页面导航">
        <a href="#overview">概览</a>
        <a href="#trend">趋势</a>
        <a href="#records">数据</a>
        <a href="#method">口径</a>
      </nav>
      <t-tag theme="success" variant="light-outline" size="small">
        <span class="status-dot" />
        数据更新 {{ summary.metadata.endDate }}
      </t-tag>
    </header>

    <main class="workspace">
      <section id="overview" class="overview-band" aria-labelledby="page-title">
        <div class="title-block">
          <p class="eyebrow">教材 P92 · 实战演练</p>
          <div class="title-row">
            <h1 id="page-title">比亚迪股票价格走势分析</h1>
            <t-tag variant="outline" size="medium">002594.SZ</t-tag>
          </div>
          <p class="subtitle">
            后复权日频行情 · 2023-01-03 至 {{ summary.metadata.endDate }} ·
            {{ summary.metadata.tradingDays }} 个交易日
          </p>
        </div>

        <div class="quote-block">
          <span class="quote-label">最新收盘 / CNY</span>
          <div class="quote-value">
            {{ formatNumber(latestRecord["收盘"]) }}
            <span :class="['signed', latestUp ? 'up' : 'down']">
              {{ signed(latestRecord["涨跌幅"]) }}%
            </span>
          </div>
          <span class="quote-note">{{ latestRecord["日期"] }} · 后复权口径</span>
        </div>
      </section>

      <section class="control-band" aria-label="图表筛选条件">
        <div class="control-group period-control">
          <span class="control-label">
            时间范围
            <t-tooltip content="快捷窗口以最新交易日为终点；起止日期均包含在样本内。">
              <button class="icon-help" type="button" aria-label="时间范围说明">
                <InfoCircleFilledIcon size="15px" />
              </button>
            </t-tooltip>
          </span>
          <t-radio-group
            :value="selectedPeriod"
            :options="periodOptions"
            variant="default-filled"
            @change="applyPeriod"
          />
        </div>

        <div class="control-divider" aria-hidden="true" />

        <div class="control-group date-control">
          <span class="control-label">自定义区间</span>
          <t-date-range-picker
            :value="dateRange"
            value-type="YYYY-MM-DD"
            format="YYYY-MM-DD"
            :range="[firstDate, lastDate]"
            :clearable="false"
            @change="onCustomRange"
          >
            <template #prefix-icon><CalendarIcon /></template>
          </t-date-range-picker>
        </div>

        <div class="control-actions">
          <t-tooltip content="复位到完整 2023-2026 周期">
            <t-button
              theme="default"
              variant="outline"
              shape="square"
              aria-label="复位时间范围"
              @click="resetRange"
            >
              <template #icon><RefreshIcon /></template>
            </t-button>
          </t-tooltip>
          <t-button theme="default" variant="outline" @click="exportCsv">
            <template #icon><DownloadIcon /></template>
            导出区间 CSV
          </t-button>
        </div>
      </section>

      <div class="range-caption">
        <span>{{ rangeLabel }}</span>
        <span>{{ filtered.length }} 条观测</span>
        <span>红涨绿跌 · 后复权</span>
      </div>

      <section class="kpi-grid" aria-label="区间关键指标">
        <article
          v-for="card in metricCards"
          :key="card.label"
          class="kpi-cell"
        >
          <div class="kpi-label">
            {{ card.label }}
            <t-tooltip v-if="card.help" :content="card.help">
              <button class="icon-help" type="button" :aria-label="`${card.label}说明`">
                <InfoCircleFilledIcon size="14px" />
              </button>
            </t-tooltip>
          </div>
          <strong :class="['kpi-value', card.tone]">{{ card.value }}</strong>
          <span class="kpi-note">{{ card.note }}</span>
        </article>
      </section>

      <section id="trend" class="analysis-grid">
        <article class="panel chart-panel">
          <div class="panel-heading chart-heading">
            <div>
              <p class="panel-kicker">PRICE ACTION</p>
              <h2>价格与成交</h2>
            </div>
            <t-tabs
              v-model="chartMode"
              size="small"
              variant="card"
            >
              <t-tab-panel
                v-for="option in chartModeOptions"
                :key="option.value"
                :value="option.value"
                :label="option.label"
              />
            </t-tabs>
          </div>

          <div class="chart-toolbar">
            <div class="ma-controls">
              <t-switch v-model="showMA" size="small" />
              <span>叠加均线</span>
              <t-select
                v-model="maPreset"
                :options="maOptions"
                :disabled="!showMA"
                size="small"
                style="width: 190px"
              />
            </div>
            <span class="chart-hint">滚轮缩放 · 拖拽查看 · 悬停读数</span>
          </div>

          <EChart
            :option="priceChartOption"
            :height="510"
            aria-label="比亚迪价格趋势主图"
          />
        </article>

        <aside class="side-column">
          <article class="panel compact-panel">
            <div class="panel-heading">
              <div>
                <p class="panel-kicker">ANNUAL RETURN</p>
                <h2>年度收益</h2>
              </div>
              <t-tag size="small" variant="light">完整周期</t-tag>
            </div>
            <EChart
              :option="annualChartOption"
              :height="230"
              aria-label="年度涨跌幅柱状图"
            />
          </article>

          <article class="panel compact-panel">
            <div class="panel-heading">
              <div>
                <p class="panel-kicker">RISK LENS</p>
                <h2>区间风险</h2>
              </div>
              <span class="risk-number">{{ metrics.drawdown.toFixed(1) }}%</span>
            </div>
            <dl class="fact-list">
              <div v-for="fact in riskFacts" :key="fact.label">
                <dt>{{ fact.label }}</dt>
                <dd>{{ fact.value }}</dd>
              </div>
            </dl>
          </article>
        </aside>
      </section>

      <section class="secondary-grid">
        <article class="panel monthly-panel">
          <div class="panel-heading">
            <div>
              <p class="panel-kicker">MONTHLY LIQUIDITY</p>
              <h2>成交额与月度节奏</h2>
            </div>
            <span class="axis-legend">
              <i class="legend-bar" /> 成交额
              <i class="legend-line" /> 月度收益
            </span>
          </div>
          <EChart
            :option="monthlyChartOption"
            :height="290"
            aria-label="月度成交额与收益图"
          />
        </article>

        <article class="panel insight-panel">
          <div class="panel-heading">
            <div>
              <p class="panel-kicker">OBSERVATION</p>
              <h2>趋势判读</h2>
            </div>
            <t-tag theme="warning" variant="light-outline" size="small">
              描述性分析
            </t-tag>
          </div>
          <ol class="insight-list">
            <li v-for="(item, index) in insightItems" :key="item">
              <span>{{ String(index + 1).padStart(2, "0") }}</span>
              <p>{{ item }}</p>
            </li>
          </ol>
        </article>
      </section>

      <section id="records" class="panel table-panel">
        <div class="panel-heading table-heading">
          <div>
            <p class="panel-kicker">OBSERVATIONS</p>
            <h2>区间行情明细</h2>
          </div>
          <div class="table-actions">
            <t-tag variant="light" size="small">{{ filtered.length }} 行</t-tag>
            <t-button theme="default" variant="text" @click="exportCsv">
              <template #icon><DownloadIcon /></template>
              下载当前区间
            </t-button>
          </div>
        </div>

        <div class="table-wrap">
          <t-table
            row-key="日期"
            :data="pagedRows"
            :columns="tableColumns"
            :hover="true"
            :stripe="true"
            :disable-data-page="true"
            size="small"
            table-layout="fixed"
          >
            <template #changeCell="{ row }">
              <span :class="['signed', row['涨跌幅'] >= 0 ? 'up' : 'down']">
                {{ signed(row["涨跌幅"]) }}%
              </span>
            </template>
            <template #volumeCell="{ row }">
              {{ formatNumber(row["成交量"], 2) }}
            </template>
            <template #amountCell="{ row }">
              {{ formatNumber(row["成交额"], 2) }}
            </template>
            <template #turnoverCell="{ row }">
              {{ formatNumber(row["换手率"]) }}%
            </template>
          </t-table>
        </div>

        <div class="pagination-row">
          <span>
            第 {{ currentPage }} 页 ·
            显示 {{ (currentPage - 1) * pageSize + 1 }}–{{
              Math.min(currentPage * pageSize, filtered.length)
            }}
          </span>
          <t-pagination
            :current="currentPage"
            :total="filtered.length"
            :page-size="pageSize"
            :page-size-options="[10, 20, 50]"
            :show-page-size="true"
            @current-change="onPageChange"
            @page-size-change="onPageSizeChange"
          />
        </div>
      </section>

      <section id="method" class="method-band">
        <div>
          <p class="panel-kicker">METHOD & SOURCE</p>
          <h2>口径与数据质量</h2>
        </div>
        <div class="method-grid">
          <p>
            <strong>价格口径</strong>
            {{ summary.metadata.priceBasis }}。2023 年原表与东财接口重合
            {{ summary.validation.overlapRows }} 行，OHLC、成交量额及换手率逐字段差异均为 0。
          </p>
          <p>
            <strong>指标口径</strong>
            区间收益按首末收盘价；年化波动率使用日收益标准差 × √252；最大回撤按运行峰值计算。
          </p>
          <p>
            <strong>扩展数据</strong>
            东方财富历史行情接口，证券代码 002594，日频、后复权，截止
            {{ summary.metadata.endDate }}。2026 年为年内数据。
          </p>
          <p>
            <strong>使用边界</strong>
            图表与结论用于课程分析和历史描述，不构成投资建议。成交量单位为手，成交额单位为人民币。
          </p>
        </div>
        <a
          class="excel-download"
          href="./downloads/比亚迪股票价格走势分析_2023-2026.xlsx"
          download
        >
          <DownloadIcon size="18px" />
          下载完整 Excel 分析工作簿
        </a>
      </section>
    </main>

    <footer class="footer">
      <span>BYD Lens · 教材 P92 实战演练</span>
      <span>数据日期 {{ summary.metadata.endDate }} · 由原始表与公开行情重建</span>
    </footer>
  </div>
</template>
