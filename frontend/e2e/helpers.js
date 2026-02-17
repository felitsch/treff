/**
 * Shared E2E test helpers for TREFF Post-Generator.
 *
 * Provides login utility, auth verification, and common selectors
 * used across all test files.
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
 * Ensure the page is authenticated and not redirected to login.
 * If the page ends up on /login, it re-authenticates.
 *
 * Use this in tests that depend on the shared auth storageState,
 * to guard against rate-limiting or expired tokens forcing a redirect.
 *
 * @param {import('@playwright/test').Page} page
 * @param {string} targetUrl - The URL to navigate to after auth check
 */
export async function ensureAuthenticated(page, targetUrl) {
  await page.goto(targetUrl)
  await page.waitForTimeout(2000)

  // If redirected to login, re-authenticate with retry
  if (page.url().includes('/login')) {
    // Wait a moment for any rate-limit window to clear
    await page.waitForTimeout(1000)
    await page.goto('/login')
    await page.waitForTimeout(500)
    await page.fill('#email', 'admin@treff.de')
    await page.fill('#password', 'treff2024')
    await page.click('[data-testid="login-submit"]')

    // Wait for redirect to /home or retry if error
    try {
      await page.waitForURL('**/home', { timeout: 15000 })
    } catch {
      // If login fails (e.g. rate limit), wait and retry once
      await page.waitForTimeout(3000)
      await page.goto('/login')
      await page.waitForTimeout(500)
      await page.fill('#email', 'admin@treff.de')
      await page.fill('#password', 'treff2024')
      await page.click('[data-testid="login-submit"]')
      await page.waitForURL('**/home', { timeout: 15000 })
    }

    await page.goto(targetUrl)
    await page.waitForTimeout(2000)
  }
}

/**
 * Dismiss the tour overlay if present on the page.
 * Handles multiple tour dismiss strategies (close button, Escape key).
 *
 * @param {import('@playwright/test').Page} page
 */
export async function dismissTourIfPresent(page) {
  // Try "Tour ueberspringen" button first (used by OnboardingTour, TourSystem, VideoWorkflowTour)
  // Use force:true because the tour overlay may intercept pointer events
  const skipBtn = page.locator('button:has-text("Tour ueberspringen")').first()
  if (await skipBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
    await skipBtn.click({ force: true })
    await page.waitForTimeout(800)
    // Check if tour is actually gone; if not, try again
    if (await skipBtn.isVisible({ timeout: 500 }).catch(() => false)) {
      await skipBtn.click({ force: true })
      await page.waitForTimeout(500)
    }
    return
  }

  // Try close/skip button variants
  const tourClose = page.locator(
    '[data-testid="tour-system"] button:has-text("Schliessen"), ' +
    '[data-testid="tour-system"] button:has-text("Skip"), ' +
    '[data-testid="tour-system"] button:has-text("×"), ' +
    '[data-testid="tour-close"]'
  ).first()
  if (await tourClose.isVisible({ timeout: 1000 }).catch(() => false)) {
    await tourClose.click({ force: true })
    await page.waitForTimeout(500)
    return
  }

  // Try Escape key as fallback
  const tourSystem = page.locator('[data-testid="tour-system"]')
  if (await tourSystem.isVisible({ timeout: 500 }).catch(() => false)) {
    await page.keyboard.press('Escape')
    await page.waitForTimeout(500)
  }
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
