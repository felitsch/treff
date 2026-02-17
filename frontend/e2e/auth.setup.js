/**
 * Global authentication setup for E2E tests.
 *
 * Logs in once and saves browser storage state (localStorage with JWT tokens)
 * so all subsequent tests can reuse the authenticated session without
 * repeating the login flow and hitting rate limits.
 */
import { test as setup, expect } from '@playwright/test'
import path from 'path'

const authFile = path.join(import.meta.dirname, '..', 'test-results', '.auth', 'user.json')

setup('authenticate', async ({ page }) => {
  // Perform login
  await page.goto('/login')
  await page.fill('#email', 'admin@treff.de')
  await page.fill('#password', 'treff2024')
  await page.click('[data-testid="login-submit"]')
  await page.waitForURL('**/home', { timeout: 15000 })

  // Verify login succeeded
  await expect(page.locator('header')).toContainText('TREFF Admin', { timeout: 5000 })

  // Save storage state (includes localStorage with JWT tokens)
  await page.context().storageState({ path: authFile })
})

export { authFile }
