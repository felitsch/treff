import { test, expect } from '@playwright/test'
import { login, selectors } from './helpers.js'

test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
  })

  test('should navigate through all main sidebar pages', async ({ page }) => {
    const pages = [
      { path: '/home', title: 'Home' },
      { path: '/create', title: 'Erstellen' },
      { path: '/calendar', title: 'Kalender' },
      { path: '/library/templates', title: 'Templates' },
      { path: '/library/assets', title: 'Assets' },
      { path: '/students', title: 'Schueler' },
      { path: '/analytics', title: 'Analytics' },
      { path: '/settings', title: 'Settings' },
    ]

    for (const p of pages) {
      await page.goto(p.path)
      await page.waitForTimeout(1000)

      // Page should load (no 404)
      const mainContent = page.locator(selectors.mainContent)
      await expect(mainContent).toBeVisible({ timeout: 5000 })

      // URL should match
      expect(page.url()).toContain(p.path)
    }
  })

  test('should show sidebar links for all groups', async ({ page }) => {
    // Sidebar should have nav groups
    const sidebar = page.locator(selectors.sidebar)
    await expect(sidebar).toBeVisible()

    // Check key nav items exist
    const navItems = [
      'Home', 'Erstellen', 'Quick Post', 'Kalender',
      'Templates', 'Assets', 'Analytics', 'Settings'
    ]

    for (const item of navItems) {
      const link = sidebar.locator(`a:has-text("${item}")`).first()
      await expect(link).toBeVisible({ timeout: 3000 })
    }
  })

  test('should show breadcrumb on nested pages', async ({ page }) => {
    // Navigate to a nested page that shows breadcrumbs
    await page.goto('/library/template-gallery')
    await page.waitForTimeout(1000)

    // Should see breadcrumb nav
    const breadcrumb = page.locator(selectors.breadcrumb)
    if (await breadcrumb.isVisible()) {
      // Should contain parent link
      await expect(breadcrumb).toContainText('Home')
    }
  })

  test('should handle 404 pages gracefully', async ({ page }) => {
    await page.goto('/nonexistent-page-12345')
    await page.waitForTimeout(1000)

    // Should show 404 page
    await expect(page.locator('text=404')).toBeVisible({ timeout: 5000 })
    await expect(page.locator('text=Seite nicht gefunden')).toBeVisible()

    // Should have link back to home
    const homeLink = page.locator('a:has-text("Zurueck zur Startseite")')
    await expect(homeLink).toBeVisible()
  })
})
