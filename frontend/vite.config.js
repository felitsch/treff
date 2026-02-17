import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// ── Performance-Optimierung Frontend (Feature #272) ──────────────
// - Code-splitting for large dependencies (Chart.js, FullCalendar, etc.)
// - Build minification and tree-shaking
// - Asset optimization with hash-based cache busting
// - Gzip-ready output with chunk size warnings
// - Bundle analysis via: npm run build -- --mode analyze

// Optional bundle visualizer (run: ANALYZE=true npm run build)
const plugins = [vue()]
if (process.env.ANALYZE === 'true') {
  const { visualizer } = await import('rollup-plugin-visualizer')
  plugins.push(
    visualizer({
      open: true,
      filename: 'dist/bundle-stats.html',
      gzipSize: true,
      brotliSize: true,
      template: 'treemap',
    })
  )
}

export default defineConfig({
  plugins,
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api/uploads': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/uploads': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },

  // ── Build optimizations ─────────────────────────────────────────
  build: {
    // Target modern browsers for smaller bundles
    target: 'es2020',

    // Increase chunk size warning limit (250kB default is too aggressive)
    chunkSizeWarningLimit: 500,

    // Enable CSS code splitting (each async route gets its own CSS)
    cssCodeSplit: true,

    // Minification
    minify: 'esbuild',

    // Source maps only in development
    sourcemap: false,

    // Rollup options for manual chunk splitting
    rollupOptions: {
      output: {
        // ── Manual code-splitting for large dependencies ──
        manualChunks: {
          // Vue core (vue, vue-router, pinia)
          'vendor-vue': ['vue', 'vue-router', 'pinia'],

          // Chart.js + vue-chartjs (heavy ~200kB)
          'vendor-charts': ['chart.js', 'vue-chartjs'],

          // FullCalendar (heavy ~300kB)
          'vendor-calendar': [
            '@fullcalendar/core',
            '@fullcalendar/daygrid',
            '@fullcalendar/interaction',
            '@fullcalendar/timegrid',
            '@fullcalendar/vue3',
          ],

          // Utilities (axios, jszip, html2canvas)
          'vendor-utils': ['axios', 'jszip'],
        },

        // Asset file naming with content hash for cache busting
        assetFileNames: (assetInfo) => {
          // CSS files
          if (assetInfo.name && assetInfo.name.endsWith('.css')) {
            return 'assets/css/[name]-[hash][extname]'
          }
          // Images
          if (assetInfo.name && /\.(png|jpe?g|svg|gif|webp|ico)$/.test(assetInfo.name)) {
            return 'assets/img/[name]-[hash][extname]'
          }
          // Fonts
          if (assetInfo.name && /\.(woff2?|eot|ttf|otf)$/.test(assetInfo.name)) {
            return 'assets/fonts/[name]-[hash][extname]'
          }
          return 'assets/[name]-[hash][extname]'
        },

        // JS chunk naming
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
      },
    },
  },

  // ── CSS optimization ────────────────────────────────────────────
  css: {
    devSourcemap: false,
  },

  // ── Dependency optimization (faster dev startup) ────────────────
  optimizeDeps: {
    include: [
      'vue',
      'vue-router',
      'pinia',
      'axios',
      'chart.js',
      'vue-chartjs',
    ],
  },
})
