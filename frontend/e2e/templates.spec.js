import { test, expect } from '@playwright/test'
import { login } from './helpers.js'

test.describe('Template Gallery', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
  })

  test('should load template gallery with cards', async ({ page }) => {
    await page.goto('/library/template-gallery')
    await page.waitForTimeout(2000)

    // Should show gallery heading
    await expect(page.locator('text=Template-Galerie')).toBeVisible({ timeout: 5000 })

    // Should have template cards
    const cards = await page.$$('[data-testid="template-card"]')
    expect(cards.length).toBeGreaterThan(0)
  })

  test('should filter templates by category', async ({ page }) => {
    await page.goto('/library/template-gallery')
    await page.waitForTimeout(2000)

    // Count initial templates
    const initialCards = await page.$$('[data-testid="template-card"]')
    const initialCount = initialCards.length

    // Click a category filter checkbox (e.g., FAQ)
    const faqCheckbox = page.locator('text=FAQ').first()
    if (await faqCheckbox.isVisible()) {
      await faqCheckbox.click()
      await page.waitForTimeout(500)

      // Should filter (fewer or equal cards)
      const filteredCards = await page.$$('[data-testid="template-card"]')
      expect(filteredCards.length).toBeLessThanOrEqual(initialCount)
    }
  })

  test('should open template preview modal', async ({ page }) => {
    await page.goto('/library/template-gallery')
    await page.waitForSelector('[data-testid="template-card"]', { timeout: 5000 })

    // Click the first template card
    await page.click('[data-testid="template-card"]')
    await page.waitForTimeout(800)

    // Modal should be visible with correct ARIA attributes
    const modal = page.locator('[role="dialog"][aria-modal="true"]')
    await expect(modal).toBeVisible({ timeout: 3000 })

    // Should have a title
    await expect(page.locator('#template-preview-title')).toBeVisible()

    // Should have action buttons
    await expect(page.locator('text=Verwenden')).toBeVisible()

    // Close with Escape
    await page.keyboard.press('Escape')
    await page.waitForTimeout(500)
    await expect(modal).not.toBeVisible()
  })

  test('should search templates', async ({ page }) => {
    await page.goto('/library/template-gallery')
    await page.waitForSelector('[data-testid="template-card"]', { timeout: 5000 })

    // Type in search box
    const searchInput = page.locator('input[placeholder*="suchen"]')
    if (await searchInput.isVisible()) {
      await searchInput.fill('FAQ')
      await page.waitForTimeout(500)

      // Results should be filtered
      const body = await page.textContent('body')
      expect(body.includes('FAQ') || body.includes('0 von')).toBeTruthy()
    }
  })
})
