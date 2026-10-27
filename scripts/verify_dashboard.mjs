import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { chromium } from "@playwright/test";

const baseURL = process.env.VERIFY_URL || "http://127.0.0.1:4174/";
const outputDir = path.resolve("artifacts/screenshots");
const chromePath = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
await mkdir(outputDir, { recursive: true });

const browser = await chromium.launch({
  executablePath: chromePath,
  headless: true,
  args: ["--font-render-hinting=none"],
});

const results = [];
const consoleErrors = [];
const pageErrors = [];

async function canvasStats(page) {
  return page.evaluate(() => {
    return Array.from(document.querySelectorAll("canvas")).map((canvas) => {
      const context = canvas.getContext("2d", { willReadFrequently: true });
      if (!context || canvas.width === 0 || canvas.height === 0) {
        return { width: canvas.width, height: canvas.height, painted: 0 };
      }
      const image = context.getImageData(0, 0, canvas.width, canvas.height);
      let painted = 0;
      let red = 0;
      let green = 0;
      let dark = 0;
      const colors = new Set();
      for (let index = 0; index < image.data.length; index += 32) {
        const r = image.data[index];
        const g = image.data[index + 1];
        const b = image.data[index + 2];
        const a = image.data[index + 3];
        if (a > 0) painted += 1;
        if (r > g * 1.25 && r > b * 1.25) red += 1;
        if (g > r * 1.15 && g > b * 1.05) green += 1;
        if (a > 200 && r < 90 && g < 100 && b < 110) dark += 1;
        if (colors.size < 300) colors.add(`${r},${g},${b},${a}`);
      }
      return {
        width: canvas.width,
        height: canvas.height,
        painted,
        red,
        green,
        dark,
        sampledColors: colors.size,
      };
    });
  });
}

async function validateViewport(width, height, label) {
  const context = await browser.newContext({
    viewport: { width, height },
    deviceScaleFactor: 1,
    locale: "zh-CN",
    timezoneId: "Asia/Shanghai",
  });
  const page = await context.newPage();
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(`${label}: ${message.text()}`);
  });
  page.on("pageerror", (error) => pageErrors.push(`${label}: ${error.message}`));

  await page.goto(baseURL, { waitUntil: "networkidle" });
  await page.locator("canvas").first().waitFor({ state: "visible" });
  await page.waitForTimeout(500);

  const title = await page.locator("h1").innerText();
  assert.match(title, /比亚迪股票价格走势分析/);

  const bodyMetrics = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    scrollHeight: document.documentElement.scrollHeight,
  }));
  assert.ok(
    bodyMetrics.scrollWidth <= bodyMetrics.clientWidth + 1,
    `${label}: page has horizontal overflow (${bodyMetrics.scrollWidth} > ${bodyMetrics.clientWidth})`,
  );

  const canvases = await canvasStats(page);
  assert.ok(canvases.length >= 3, `${label}: expected at least three chart canvases`);
  const aggregate = canvases.reduce(
    (total, current) => ({
      painted: total.painted + current.painted,
      red: total.red + current.red,
      green: total.green + current.green,
      dark: total.dark + current.dark,
      colors: Math.max(total.colors, current.sampledColors || 0),
    }),
    { painted: 0, red: 0, green: 0, dark: 0, colors: 0 },
  );
  assert.ok(aggregate.painted > 1000, `${label}: chart canvases appear blank`);
  assert.ok(aggregate.red > 50, `${label}: no meaningful red market pixels`);
  assert.ok(aggregate.green > 50, `${label}: no meaningful green market pixels`);
  assert.ok(aggregate.colors > 20, `${label}: chart rendering lacks color depth`);

  await page.screenshot({
    path: path.join(outputDir, `${label}.png`),
    fullPage: true,
    animations: "disabled",
  });

  results.push({
    label,
    viewport: `${width}x${height}`,
    pageWidth: bodyMetrics.clientWidth,
    pageHeight: bodyMetrics.scrollHeight,
    canvases: canvases.length,
    canvasPixels: aggregate,
  });
  await context.close();
}

await validateViewport(375, 900, "mobile-375");
await validateViewport(768, 960, "tablet-768");
await validateViewport(1024, 900, "laptop-1024");
await validateViewport(1440, 1000, "desktop-1440");

const interactionContext = await browser.newContext({
  viewport: { width: 1440, height: 1000 },
  locale: "zh-CN",
  reducedMotion: "no-preference",
});
const page = await interactionContext.newPage();
page.on("console", (message) => {
  if (message.type() === "error") consoleErrors.push(`interaction: ${message.text()}`);
});
page.on("pageerror", (error) => pageErrors.push(`interaction: ${error.message}`));
await page.goto(baseURL, { waitUntil: "networkidle" });
await page.locator("canvas").first().waitFor({ state: "visible" });

const initialRange = await page.locator(".range-caption span").first().innerText();
await page.getByText("1 年", { exact: true }).click();
await page.waitForTimeout(250);
const oneYearRange = await page.locator(".range-caption span").first().innerText();
assert.notEqual(oneYearRange, initialRange, "Period control did not change range");

await page.getByText("回撤", { exact: true }).click();
await page.waitForTimeout(250);
await page.getByText("月度收益", { exact: true }).click();
await page.waitForTimeout(250);
await page.getByText("K 线", { exact: true }).click();
await page.waitForTimeout(250);

const download = page.waitForEvent("download");
await page.getByRole("button", { name: /导出区间 CSV/ }).click();
const csvDownload = await download;
assert.match(csvDownload.suggestedFilename(), /\.csv$/);

const excelHref = await page.locator(".excel-download").getAttribute("href");
const excelUrl = new URL(excelHref, baseURL).href;
const excelResponse = await page.request.get(excelUrl);
assert.equal(excelResponse.status(), 200, "Excel workbook link is not reachable");
assert.ok(
  (await excelResponse.body()).byteLength > 20_000,
  "Excel workbook link returned an unexpectedly small file",
);

await page.screenshot({
  path: path.join(outputDir, "interaction-kline-1440.png"),
  fullPage: true,
  animations: "disabled",
});

const reducedContext = await browser.newContext({
  viewport: { width: 390, height: 844 },
  reducedMotion: "reduce",
  locale: "zh-CN",
});
const reducedPage = await reducedContext.newPage();
await reducedPage.goto(baseURL, { waitUntil: "networkidle" });
const reducedAnimation = await reducedPage.evaluate(
  () => getComputedStyle(document.documentElement).scrollBehavior,
);
assert.equal(reducedAnimation, "auto", "Reduced-motion scroll behavior not honored");
await reducedContext.close();

assert.deepEqual(pageErrors, [], `Page errors: ${pageErrors.join("; ")}`);
assert.deepEqual(consoleErrors, [], `Console errors: ${consoleErrors.join("; ")}`);

console.log(
  JSON.stringify(
    {
      baseURL,
      interaction: {
        initialRange,
        oneYearRange,
        csvDownload: csvDownload.suggestedFilename(),
        excelStatus: excelResponse.status(),
      },
      reducedMotion: reducedAnimation,
      results,
      consoleErrors,
      pageErrors,
    },
    null,
    2,
  ),
);

await interactionContext.close();
await browser.close();
