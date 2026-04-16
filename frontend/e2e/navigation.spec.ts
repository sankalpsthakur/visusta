import { test, expect } from '@playwright/test'

test.describe('Navigation', () => {
  test('root resolves to a locale-prefixed route', async ({ page }) => {
    const response = await page.goto('/')
    expect(response?.ok()).toBeTruthy()
    expect(new URL(page.url()).pathname).toMatch(/^\/[a-z]{2}\/?$/)
  })

  test('/en/ responds with HTTP 200', async ({ page }) => {
    const response = await page.goto('/en/')
    expect(response?.status()).toBe(200)
  })

  test('sidebar contains navigation links', async ({ page }) => {
    await page.goto('/en/')
    const nav = page.locator('nav, [role="navigation"], aside')
    await expect(nav.first()).toBeVisible()
  })

  test('/en/dashboard responds with HTTP 200', async ({ page }) => {
    const response = await page.goto('/en/dashboard')
    expect(response?.status()).toBe(200)
  })

  test('/en/templates responds with HTTP 200', async ({ page }) => {
    const response = await page.goto('/en/templates')
    expect(response?.status()).toBe(200)
  })

  test('unscoped routes redirect to locale-prefixed routes', async ({ page }) => {
    const routes = ['/dashboard', '/clients', '/reports', '/settings', '/audit']

    for (const route of routes) {
      const response = await page.goto(route)
      expect(response?.ok()).toBeTruthy()
      expect(new URL(page.url()).pathname).toMatch(
        new RegExp(`^/[a-z]{2}${route.replace('/', '\\/')}$`)
      )
    }
  })
})
