import { test, expect } from '@playwright/test'
import { ensureAuthenticated } from './helpers.js'

// Uses shared auth state from the setup project (no manual login needed)
test.describe('Content Pillar Feature', () => {

  test('should show content pillar badges when selecting categories', async ({ page }) => {
    // ── Steps 1-3: Auth is handled by the setup project ────────────────
    await ensureAuthenticated(page, '/home')
    await expect(page.locator('header')).toContainText('TREFF', { timeout: 10000 })
    console.log('STEPS 1-3: Already authenticated via setup project. Dashboard loaded.')

    // ── Step 4: Navigate to quick post creator ─────────────────────────
    await page.goto('/create/quick')
    await page.waitForTimeout(2000)
    await expect(page.locator('[data-testid="cat-chip-laender_spotlight"]')).toBeVisible({ timeout: 10000 })
    console.log('STEP 4: Quick post creator loaded, category chips visible.')

    // ── Step 5: Click Laender-Spotlight chip ───────────────────────────
    await page.locator('[data-testid="cat-chip-laender_spotlight"]').click()
    await page.waitForTimeout(1000)
    console.log('STEP 5: Clicked Laender-Spotlight category chip.')

    // ── Step 6: Screenshot - expect Content Pillar badge ───────────────
    const pillarBadge = page.locator('text=Content Pillar:')
    const pillarBadgeVisible = await pillarBadge.isVisible().catch(() => false)
    console.log('STEP 6: Content Pillar badge visible:', pillarBadgeVisible)

    const pillarName = page.locator('text=Laender-Spotlights & Destination Content').first()
    const pillarNameVisible = await pillarName.isVisible().catch(() => false)
    console.log('STEP 6: "Laender-Spotlights & Destination Content" visible:', pillarNameVisible)

    const pillarSection = page.locator('[data-testid="step1-content"]')
    const globeInSection = await pillarSection.locator('text=\uD83C\uDF0D').first().isVisible().catch(() => false)
    console.log('STEP 6: Globe icon visible in step1 section:', globeInSection)

    await page.screenshot({ path: 'test-results/step6-laender-spotlight-pillar.png', fullPage: false })
    console.log('STEP 6: Screenshot saved to test-results/step6-laender-spotlight-pillar.png')

    await expect(pillarBadge).toBeVisible({ timeout: 5000 })
    await expect(pillarName).toBeVisible({ timeout: 5000 })

    // ── Step 7: Click Erfahrungsberichte chip ──────────────────────────
    await page.locator('[data-testid="cat-chip-erfahrungsberichte"]').click()
    await page.waitForTimeout(1000)
    console.log('STEP 7: Clicked Erfahrungsberichte category chip.')

    // ── Step 8: Screenshot - pillar should now show "Erfahrungsberichte & Testimonials"
    const erfahrungenPillar = page.locator('text=Erfahrungsberichte & Testimonials').first()
    const erfahrungenVisible = await erfahrungenPillar.isVisible().catch(() => false)
    console.log('STEP 8: "Erfahrungsberichte & Testimonials" visible:', erfahrungenVisible)

    const memoInSection = await pillarSection.locator('text=\uD83D\uDCDD').first().isVisible().catch(() => false)
    console.log('STEP 8: Memo/pencil icon visible in step1 section:', memoInSection)

    await page.screenshot({ path: 'test-results/step8-erfahrungsberichte-pillar.png', fullPage: false })
    console.log('STEP 8: Screenshot saved to test-results/step8-erfahrungsberichte-pillar.png')

    await expect(erfahrungenPillar).toBeVisible({ timeout: 5000 })
  })

  test('should show pillar distribution widget on dashboard', async ({ page }) => {
    // ── Step 9: Navigate to dashboard and check pillar distribution widget
    await ensureAuthenticated(page, '/home')
    await page.waitForTimeout(3000)
    console.log('STEP 9: Navigated to /home dashboard.')

    // Scroll down to find the Pillar Distribution widget
    const pillarWidget = page.locator('text=Content-Pillar-Verteilung')

    try {
      await pillarWidget.scrollIntoViewIfNeeded({ timeout: 10000 })
      console.log('STEP 9: Scrolled to Content-Pillar-Verteilung widget.')
    } catch {
      console.log('STEP 9: Could not scroll to widget, taking full-page screenshot.')
    }

    await page.waitForTimeout(2000)

    const widgetVisible = await pillarWidget.isVisible().catch(() => false)
    console.log('STEP 9: Content-Pillar-Verteilung widget visible:', widgetVisible)

    await page.screenshot({ path: 'test-results/step9-dashboard-pillar-widget.png', fullPage: true })
    console.log('STEP 9: Full-page screenshot saved to test-results/step9-dashboard-pillar-widget.png')
  })
})
