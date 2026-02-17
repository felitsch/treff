import { test, expect } from '@playwright/test'
import { ensureAuthenticated } from './helpers.js'

test.describe('Create Post Flow', () => {

  test('should load the quick post creator', async ({ page }) => {
    await ensureAuthenticated(page, '/create/quick')

    // Should see the step indicator or first step content
    // Step 1: Category selection
    await expect(page.locator('text=Laender-Spotlight').first()).toBeVisible({ timeout: 10000 })
    await expect(page.locator('text=Erfahrungsberichte').first()).toBeVisible()
  })

  test('should select a category and navigate to step 2', async ({ page }) => {
    await ensureAuthenticated(page, '/create/quick')

    // Click on a category (e.g., "Laender-Spotlight")
    await expect(page.locator('text=Laender-Spotlight').first()).toBeVisible({ timeout: 10000 })
    await page.locator('text=Laender-Spotlight').first().click()
    await page.waitForTimeout(500)

    // Should show step 2 content (templates)
    // The step indicator should show step 2 or template selection should be visible
    const pageContent = await page.textContent('body')
    // After selecting a category, the user should see template options or the next step
    expect(
      pageContent.includes('Template') ||
      pageContent.includes('Vorlage') ||
      pageContent.includes('Design')
    ).toBeTruthy()
  })

  test('should load the post creator hub', async ({ page }) => {
    await ensureAuthenticated(page, '/create')

    // Should see creation options in main content
    await expect(page.locator('#main-content').first()).toBeVisible({ timeout: 10000 })
    // Should see the "Content erstellen" heading or creation options
    const pageContent = await page.textContent('#main-content')
    expect(
      pageContent.includes('Quick Post') ||
      pageContent.includes('Content erstellen') ||
      pageContent.includes('Erstellen')
    ).toBeTruthy()
  })
})
