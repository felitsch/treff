/**
 * Shared E2E test helpers for TREFF Post-Generator.
 *
 * Provides login utility and common selectors used across all test files.
 */

/**
 * Login to the application.
 * @param {import('@playwright/test').Page} page
 * @param {string} email
 * @param {string} password
 */
export async function login(page, email = 'admin@treff.de', password = 'treff2024') {
  await page.goto('/login')
  await page.fill('#email', email)
  await page.fill('#password', password)
  await page.click('[data-testid="login-submit"]')
  await page.waitForURL('**/home', { timeout: 15000 })
}

/**
 * Common selectors used throughout tests.
 */
export const selectors = {
  sidebar: 'nav[aria-label="Hauptnavigation"]',
  mainContent: '#main-content',
  skipToContent: '[data-testid="skip-to-content"]',
  loginSubmit: '[data-testid="login-submit"]',
  breadcrumb: '[data-testid="breadcrumb-nav"]',
  toastContainer: '[role="status"][aria-live="polite"]',
}
