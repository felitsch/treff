import { test, expect } from '@playwright/test'
import { login, selectors } from './helpers.js'

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
  })

  test('should load dashboard with all widgets', async ({ page }) => {
    // Page title
    await expect(page.locator('h1')).toContainText('Home')

    // Greeting message
    await expect(page.locator('text=Guten')).toBeVisible({ timeout: 5000 })

    // Stats cards (Posts this week, Scheduled, Drafts)
    await expect(page.locator('text=Posts diese Woche')).toBeVisible()
    await expect(page.locator('text=Geplante Posts')).toBeVisible()
    await expect(page.locator('text=Entwuerfe')).toBeVisible()

    // Quick action cards
    await expect(page.locator('text=Neuer Post')).toBeVisible()
    await expect(page.locator('text=Aus Template')).toBeVisible()
  })

  test('should load without JavaScript errors', async ({ page }) => {
    const errors = []
    page.on('console', msg => {
      if (msg.type() === 'error') errors.push(msg.text())
    })

    await page.goto('/home')
    await page.waitForTimeout(2000)

    // Filter out non-app errors (network, favicon, etc.)
    const appErrors = errors.filter(
      e => !e.includes('favicon') && !e.includes('404') && !e.includes('net::')
    )
    expect(appErrors).toHaveLength(0)
  })

  test('should navigate to create post from quick action', async ({ page }) => {
    await page.click('text=Neuer Post')
    await page.waitForURL('**/create/quick', { timeout: 5000 })
    expect(page.url()).toContain('/create/quick')
  })
})
