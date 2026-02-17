import { test, expect } from '@playwright/test'
import { ensureAuthenticated, selectors } from './helpers.js'

test.describe('Dashboard', () => {
  test('should load dashboard with greeting and quick actions', async ({ page }) => {
    await ensureAuthenticated(page, '/home')

    // Page heading in main content area
    await expect(page.locator('#main-content').first()).toBeVisible({ timeout: 10000 })

    // Greeting message (always rendered client-side)
    await expect(page.locator('text=Guten').first()).toBeVisible({ timeout: 5000 })

    // Sidebar should be visible
    await expect(page.locator(selectors.sidebar)).toBeVisible()

    // Quick action cards (rendered client-side)
    await expect(page.locator('text=Neuer Post').first()).toBeVisible({ timeout: 5000 })
    await expect(page.locator('text=Aus Template').first()).toBeVisible()

    // Click "Neuer Post" to navigate
    await page.locator('text=Neuer Post').first().click()
    await page.waitForURL('**/create/**', { timeout: 5000 })
    expect(page.url()).toContain('/create/')
  })
})
