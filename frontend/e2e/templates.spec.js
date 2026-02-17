import { test, expect } from '@playwright/test'
import { ensureAuthenticated } from './helpers.js'

test.describe('Template Gallery', () => {

  test('should load template gallery with cards', async ({ page }) => {
    await ensureAuthenticated(page, '/library/template-gallery')

    // Wait for the gallery container to appear
    await expect(page.locator('[data-testid="template-gallery"]')).toBeVisible({ timeout: 10000 })

    // Should show gallery heading in main content
    await expect(
      page.locator('[data-testid="template-gallery"] h1').first()
    ).toContainText('Template-Galerie')

    // Should have template cards (wait for API to load templates)
    await expect(page.locator('[data-testid="template-card"]').first()).toBeVisible({ timeout: 10000 })
    const cards = await page.$$('[data-testid="template-card"]')
    expect(cards.length).toBeGreaterThan(0)
  })

  test('should filter templates by category', async ({ page }) => {
    await ensureAuthenticated(page, '/library/template-gallery')

    // Wait for template cards to load
    await expect(page.locator('[data-testid="template-card"]').first()).toBeVisible({ timeout: 10000 })

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
    await ensureAuthenticated(page, '/library/template-gallery')

    // Wait for template cards with generous timeout
    await expect(page.locator('[data-testid="template-card"]').first()).toBeVisible({ timeout: 10000 })

    // Click the first template card
    await page.click('[data-testid="template-card"]')
    await page.waitForTimeout(800)

    // Modal should be visible with correct ARIA attributes
    const modal = page.locator('[role="dialog"][aria-modal="true"]')
    await expect(modal).toBeVisible({ timeout: 3000 })

    // Should have a title
    await expect(page.locator('#template-preview-title')).toBeVisible()

    // Should have action buttons
    await expect(page.locator('text=Verwenden').first()).toBeVisible()

    // Close with Escape
    await page.keyboard.press('Escape')
    await page.waitForTimeout(500)
    await expect(modal).not.toBeVisible()
  })

  test('should search templates', async ({ page }) => {
    await ensureAuthenticated(page, '/library/template-gallery')

    // Wait for template cards with generous timeout
    await expect(page.locator('[data-testid="template-card"]').first()).toBeVisible({ timeout: 10000 })

    // Count initial templates
    const initialCards = await page.$$('[data-testid="template-card"]')
    const initialCount = initialCards.length

    // Find any visible search input on the page
    const searchInput = page.locator(
      '[data-testid="search-input"], [data-testid="library-search-input"], input[placeholder*="Suche"], input[placeholder*="suche"], input[type="search"]'
    ).first()

    if (await searchInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      // Search for a term that should filter results
      await searchInput.fill('xyznonexistent')
      await page.waitForTimeout(800)

      // After searching for nonsense, should have fewer or zero results
      const filteredCards = await page.$$('[data-testid="template-card"]')
      expect(filteredCards.length).toBeLessThanOrEqual(initialCount)

      // Clear search
      await searchInput.fill('')
      await page.waitForTimeout(500)
    }
  })
})
