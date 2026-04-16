# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: navigation.spec.ts >> Navigation >> unscoped routes redirect to locale-prefixed routes
- Location: e2e/navigation.spec.ts:31:7

# Error details

```
Error: expect(received).toBeTruthy()

Received: false
```

# Page snapshot

```yaml
- generic [ref=e2]: Internal Server Error
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test'
  2  | 
  3  | test.describe('Navigation', () => {
  4  |   test('root resolves to a locale-prefixed route', async ({ page }) => {
  5  |     const response = await page.goto('/')
  6  |     expect(response?.ok()).toBeTruthy()
  7  |     expect(new URL(page.url()).pathname).toMatch(/^\/[a-z]{2}\/?$/)
  8  |   })
  9  | 
  10 |   test('/en/ responds with HTTP 200', async ({ page }) => {
  11 |     const response = await page.goto('/en/')
  12 |     expect(response?.status()).toBe(200)
  13 |   })
  14 | 
  15 |   test('sidebar contains navigation links', async ({ page }) => {
  16 |     await page.goto('/en/')
  17 |     const nav = page.locator('nav, [role="navigation"], aside')
  18 |     await expect(nav.first()).toBeVisible()
  19 |   })
  20 | 
  21 |   test('/en/dashboard responds with HTTP 200', async ({ page }) => {
  22 |     const response = await page.goto('/en/dashboard')
  23 |     expect(response?.status()).toBe(200)
  24 |   })
  25 | 
  26 |   test('/en/templates responds with HTTP 200', async ({ page }) => {
  27 |     const response = await page.goto('/en/templates')
  28 |     expect(response?.status()).toBe(200)
  29 |   })
  30 | 
  31 |   test('unscoped routes redirect to locale-prefixed routes', async ({ page }) => {
  32 |     const routes = ['/dashboard', '/clients', '/reports', '/settings', '/audit']
  33 | 
  34 |     for (const route of routes) {
  35 |       const response = await page.goto(route)
> 36 |       expect(response?.ok()).toBeTruthy()
     |                              ^ Error: expect(received).toBeTruthy()
  37 |       expect(new URL(page.url()).pathname).toMatch(
  38 |         new RegExp(`^/[a-z]{2}${route.replace('/', '\\/')}$`)
  39 |       )
  40 |     }
  41 |   })
  42 | })
  43 | 
```