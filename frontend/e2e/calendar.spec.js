import { test, expect } from '@playwright/test'
import { login } from './helpers.js'

test.describe('Calendar View', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
  })

  test('should load calendar page', async ({ page }) => {
    await page.goto('/calendar')
    await page.waitForTimeout(2000)

    // Should show calendar heading
    await expect(page.locator('h1')).toContainText('Kalender')

    // Should have the FullCalendar component rendered
    const calendarEl = page.locator('.fc')
    await expect(calendarEl).toBeVisible({ timeout: 5000 })
  })

  test('should switch between calendar views', async ({ page }) => {
    await page.goto('/calendar')
    await page.waitForSelector('.fc', { timeout: 5000 })

    // Look for view switching buttons (month/week/day)
    const monthBtn = page.locator('button:has-text("Monat")')
    const weekBtn = page.locator('button:has-text("Woche")')

    if (await monthBtn.isVisible()) {
      await monthBtn.click()
      await page.waitForTimeout(500)
      // Should show month view
      await expect(page.locator('.fc')).toBeVisible()
    }

    if (await weekBtn.isVisible()) {
      await weekBtn.click()
      await page.waitForTimeout(500)
      // Should show week view
      await expect(page.locator('.fc')).toBeVisible()
    }
  })

  test('should navigate between months', async ({ page }) => {
    await page.goto('/calendar')
    await page.waitForSelector('.fc', { timeout: 5000 })

    // Get current title
    const title = page.locator('.fc-toolbar-title')
    const initialTitle = await title.textContent()

    // Click next month button
    const nextBtn = page.locator('.fc-next-button')
    if (await nextBtn.isVisible()) {
      await nextBtn.click()
      await page.waitForTimeout(500)
      const newTitle = await title.textContent()
      expect(newTitle).not.toBe(initialTitle)
    }
  })
})
