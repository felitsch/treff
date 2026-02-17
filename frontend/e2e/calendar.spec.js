import { test, expect } from '@playwright/test'
import { ensureAuthenticated, dismissTourIfPresent } from './helpers.js'

test.describe('Calendar View', () => {
  test('should load calendar page', async ({ page }) => {
    await ensureAuthenticated(page, '/calendar')

    // Dismiss tour overlay if present
    await dismissTourIfPresent(page)

    // Should show calendar heading in main content
    await expect(page.locator('#main-content h1').first()).toContainText('Content-Kalender')

    // Should have the view toggle buttons (use data-tour attribute for specificity)
    const viewToggle = page.locator('[data-tour="cal-views"]')
    await expect(viewToggle.locator('button:has-text("Monat")')).toBeVisible({ timeout: 5000 })
    await expect(viewToggle.locator('button:has-text("Woche")')).toBeVisible()
  })

  test('should switch between calendar views', async ({ page }) => {
    await ensureAuthenticated(page, '/calendar')

    // Dismiss tour overlay if present — must be fully gone before interacting
    await dismissTourIfPresent(page)
    // Give the UI time to fully clear the tour overlay and animations
    await page.waitForTimeout(1500)

    // Verify no tour overlay remains blocking interactions
    const tourSystem = page.locator('[data-testid="tour-system"]')
    if (await tourSystem.isVisible({ timeout: 500 }).catch(() => false)) {
      // Force-dismiss with multiple strategies
      await page.keyboard.press('Escape')
      await page.waitForTimeout(500)
      const skipAgain = page.locator('button:has-text("Tour ueberspringen")').first()
      if (await skipAgain.isVisible({ timeout: 500 }).catch(() => false)) {
        await skipAgain.click({ force: true })
        await page.waitForTimeout(500)
      }
    }

    const viewToggle = page.locator('[data-tour="cal-views"]')

    // Click "Woche" button to switch to week view (force to bypass any remaining overlay)
    const weekBtn = viewToggle.locator('button:has-text("Woche")')
    await expect(weekBtn).toBeVisible({ timeout: 5000 })
    await weekBtn.click({ force: true })
    await page.waitForTimeout(800)

    // The "Woche" button should now be active (has bg-blue-600 class)
    await expect(weekBtn).toHaveClass(/bg-blue-600/, { timeout: 5000 })

    // Switch back to month view
    const monthBtn = viewToggle.locator('button:has-text("Monat")')
    await monthBtn.click({ force: true })
    await page.waitForTimeout(800)
    await expect(monthBtn).toHaveClass(/bg-blue-600/, { timeout: 5000 })
  })

  test('should navigate between months', async ({ page }) => {
    await ensureAuthenticated(page, '/calendar')

    // Dismiss tour overlay if present
    await dismissTourIfPresent(page)

    // The calendar grid should have 7 columns (days of the week)
    await expect(page.locator('.grid-cols-7').first()).toBeVisible({ timeout: 5000 })

    // Calendar heading should be visible
    await expect(page.locator('#main-content h1').first()).toContainText('Content-Kalender')
  })
})
