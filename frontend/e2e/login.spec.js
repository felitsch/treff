import { test, expect } from '@playwright/test'
import { login, selectors } from './helpers.js'

test.describe('Login Flow', () => {
  test('should display login form with correct labels', async ({ page }) => {
    await page.goto('/login')

    // Check form elements exist
    await expect(page.locator('label[for="email"]')).toBeVisible()
    await expect(page.locator('label[for="password"]')).toBeVisible()
    await expect(page.locator(selectors.loginSubmit)).toBeVisible()
    await expect(page.locator('h1')).toContainText('TREFF')
  })

  test('should show error on invalid credentials', async ({ page }) => {
    await page.goto('/login')
    await page.fill('#email', 'wrong@treff.de')
    await page.fill('#password', 'wrongpassword')
    await page.click(selectors.loginSubmit)

    // Should show error message
    await expect(page.locator('[role="alert"]')).toBeVisible({ timeout: 5000 })
    // Should stay on login page
    expect(page.url()).toContain('/login')
  })

  test('should login successfully and redirect to dashboard', async ({ page }) => {
    await login(page)

    // Should be on the home/dashboard page
    expect(page.url()).toContain('/home')

    // Should show user info in header
    await expect(page.locator('header')).toContainText('TREFF Admin')

    // Should see sidebar navigation
    await expect(page.locator(selectors.sidebar)).toBeVisible()
  })

  test('should redirect unauthenticated users to login', async ({ page }) => {
    await page.goto('/home')
    // Should redirect to login
    await page.waitForURL('**/login', { timeout: 5000 })
    expect(page.url()).toContain('/login')
  })

  test('should logout and return to login page', async ({ page }) => {
    await login(page)
    await page.click('button:has-text("Logout")')
    await page.waitForURL('**/login', { timeout: 5000 })
    expect(page.url()).toContain('/login')
  })
})
