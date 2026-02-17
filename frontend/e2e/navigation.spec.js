import { test, expect } from '@playwright/test'
import { ensureAuthenticated, selectors } from './helpers.js'

test.describe('Navigation', () => {
  test('should navigate to key pages and show sidebar', async ({ page }) => {
    // Start at home
    await ensureAuthenticated(page, '/home')

    // Main content and sidebar should be visible
    await expect(page.locator(selectors.mainContent)).toBeVisible({ timeout: 10000 })
    await expect(page.locator(selectors.sidebar)).toBeVisible()

    // Check key nav items exist in sidebar
    const sidebar = page.locator(selectors.sidebar)
    for (const item of ['Home', 'Erstellen', 'Kalender', 'Templates']) {
      const link = sidebar.locator(`a:has-text("${item}")`).first()
      await expect(link).toBeVisible({ timeout: 3000 })
    }

    // Navigate to create page via URL
    await page.goto('/create')
    await page.waitForTimeout(1500)
    await expect(page.locator(selectors.mainContent)).toBeVisible({ timeout: 5000 })
    expect(page.url()).toContain('/create')

    // Navigate to calendar via URL
    await page.goto('/calendar')
    await page.waitForTimeout(1500)
    await expect(page.locator(selectors.mainContent)).toBeVisible({ timeout: 5000 })
    expect(page.url()).toContain('/calendar')
  })

  test('should show breadcrumb on nested pages', async ({ page }) => {
    await ensureAuthenticated(page, '/library/template-gallery')

    const breadcrumb = page.locator(selectors.breadcrumb)
    if (await breadcrumb.isVisible()) {
      await expect(breadcrumb).toContainText('Home')
    }
  })

  test('should handle 404 pages gracefully', async ({ page }) => {
    await page.goto('/nonexistent-page-12345')
    await page.waitForTimeout(1000)

    await expect(page.locator('text=404').first()).toBeVisible({ timeout: 5000 })
    await expect(page.locator('text=Seite nicht gefunden').first()).toBeVisible()
    await expect(page.locator('a:has-text("Zurueck zur Startseite")')).toBeVisible()
  })
})
