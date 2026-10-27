import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  base: "./",
  server: {
    port: 4173,
    strictPort: false,
  },
  build: {
    target: "es2022",
    outDir: "dist",
    sourcemap: false,
    chunkSizeWarningLimit: 1400,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("node_modules/echarts") || id.includes("node_modules/zrender")) {
            return "charts";
          }
          if (id.includes("node_modules/tdesign")) {
            return "tdesign";
          }
          if (id.includes("node_modules/vue")) {
            return "vue";
          }
        },
      },
    },
  },
});
