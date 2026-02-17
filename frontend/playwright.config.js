import { defineConfig, devices } from '@playwright/test'
import path from 'path'

const authFile = path.join(import.meta.dirname, 'test-results', '.auth', 'user.json')

/**
 * Playwright E2E Test Configuration for TREFF Post-Generator.
 *
 * Run all tests:   npx playwright test
 * Run with UI:     npx playwright test --ui
 * Run specific:    npx playwright test e2e/login.spec.js
 * Debug:           npx playwright test --debug
 *
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false, // Run tests sequentially (shared auth state)
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1,
  workers: 1, // Single worker to avoid port conflicts
  reporter: process.env.CI ? 'github' : 'html',

  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    locale: 'de-DE',
  },

  projects: [
    // Setup project — authenticates once and saves storage state
    {
      name: 'setup',
      testMatch: /auth\.setup\.js/,
    },
    // Main test project — reuses authenticated state
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        storageState: authFile,
      },
      dependencies: ['setup'],
      testIgnore: /auth\.setup\.js/,
    },
  ],

  /* Optionally start dev servers before tests */
  // webServer: [
  //   {
  //     command: 'cd ../backend && source venv/bin/activate && uvicorn app.main:app --port 8000',
  //     port: 8000,
  //     reuseExistingServer: !process.env.CI,
  //   },
  //   {
  //     command: 'npm run dev',
  //     port: 5173,
  //     reuseExistingServer: !process.env.CI,
  //   },
  // ],
})
