<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as echarts from "echarts";

const props = defineProps({
  option: {
    type: Object,
    required: true,
  },
  height: {
    type: [Number, String],
    default: 420,
  },
  ariaLabel: {
    type: String,
    default: "数据图表",
  },
});

const chartRoot = ref(null);
let chart;
let resizeObserver;

const normalizedHeight =
  typeof props.height === "number" ? `${props.height}px` : props.height;

function render() {
  if (!chart) return;
  chart.setOption(props.option, { notMerge: true, lazyUpdate: false });
}

onMounted(async () => {
  await nextTick();
  chart = echarts.init(chartRoot.value, null, {
    renderer: "canvas",
    devicePixelRatio: Math.min(window.devicePixelRatio || 1, 2),
  });
  render();

  resizeObserver = new ResizeObserver(() => {
    chart?.resize();
  });
  resizeObserver.observe(chartRoot.value);
});

watch(
  () => props.option,
  () => {
    render();
  },
  { deep: true },
);

onBeforeUnmount(() => {
  resizeObserver?.disconnect();
  chart?.dispose();
});
</script>

<template>
  <div
    ref="chartRoot"
    class="chart-canvas"
    :style="{ height: normalizedHeight }"
    role="img"
    :aria-label="ariaLabel"
  />
</template>
