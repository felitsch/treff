import { test, expect } from '@playwright/test'
import { login } from './helpers.js'

test.describe('Create Post Flow', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
  })

  test('should load the quick post creator', async ({ page }) => {
    await page.goto('/create/quick')
    await page.waitForTimeout(1000)

    // Should see the step indicator or first step content
    // Step 1: Category selection
    await expect(page.locator('text=Laender-Spotlight')).toBeVisible({ timeout: 5000 })
    await expect(page.locator('text=Erfahrungsberichte')).toBeVisible()
  })

  test('should select a category and navigate to step 2', async ({ page }) => {
    await page.goto('/create/quick')
    await page.waitForTimeout(1000)

    // Click on a category (e.g., "Laender-Spotlight")
    await page.click('text=Laender-Spotlight')
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
    await page.goto('/create')
    await page.waitForTimeout(1000)

    // Should see creation options
    await expect(page.locator('text=Quick Post')).toBeVisible({ timeout: 5000 })
  })
})
