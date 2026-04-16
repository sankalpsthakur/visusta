# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: templates.spec.ts >> Templates flows >> unknown templates show an explicit not found state
- Location: e2e/templates.spec.ts:79:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText(/template 999999 not found/i)
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for getByText(/template 999999 not found/i)

```

# Page snapshot

```yaml
- generic [ref=e2]: Internal Server Error
```

# Test source

```ts
  1  | import { expect, test } from '@playwright/test'
  2  | 
  3  | function trackClientErrors(page: import('@playwright/test').Page) {
  4  |   const pageErrors: string[] = []
  5  |   const consoleErrors: string[] = []
  6  | 
  7  |   page.on('pageerror', (error) => pageErrors.push(error.message))
  8  |   page.on('console', (message) => {
  9  |     if (message.type() === 'error') {
  10 |       consoleErrors.push(message.text())
  11 |     }
  12 |   })
  13 | 
  14 |   return { pageErrors, consoleErrors }
  15 | }
  16 | 
  17 | function expectHealthyClient(errors: { pageErrors: string[]; consoleErrors: string[] }) {
  18 |   const fatalPageErrors = errors.pageErrors.filter(
  19 |     (message) => !message.includes('ResizeObserver') && !message.includes('hydrat'),
  20 |   )
  21 |   const fatalConsoleErrors = errors.consoleErrors.filter(
  22 |     (message) =>
  23 |       !message.includes('404') &&
  24 |       !message.includes('favicon') &&
  25 |       !message.includes('ResizeObserver'),
  26 |   )
  27 | 
  28 |   expect(fatalPageErrors).toHaveLength(0)
  29 |   expect(fatalConsoleErrors).toHaveLength(0)
  30 | }
  31 | 
  32 | test.describe('Templates flows', () => {
  33 |   test('list view renders without overlays or client errors', async ({ page }) => {
  34 |     const errors = trackClientErrors(page)
  35 | 
  36 |     const response = await page.goto('/en/templates')
  37 |     expect(response?.status()).toBe(200)
  38 | 
  39 |     await expect(page.getByRole('heading', { name: 'Templates' })).toBeVisible()
  40 |     await expect(page.getByRole('button', { name: /new template/i })).toBeVisible()
  41 |     await expect(page.getByText(/failed to load templates/i)).toHaveCount(0)
  42 |     await expect(page.getByText(/This page couldn’t load/i)).toHaveCount(0)
  43 | 
  44 |     expectHealthyClient(errors)
  45 |   })
  46 | 
  47 |   test('creates a template and saves a new version through the editor', async ({ page }) => {
  48 |     const templateName = `Playwright Template ${Date.now()}`
  49 |     const errors = trackClientErrors(page)
  50 | 
  51 |     await page.goto('/en/templates')
  52 |     await page.getByRole('button', { name: /new template/i }).click()
  53 | 
  54 |     await page.getByRole('textbox', { name: 'Template name' }).fill(templateName)
  55 |     await page.getByRole('textbox', { name: 'Template description' }).fill(
  56 |       'Quarterly cross-border compliance reporting for adversarial browser verification.',
  57 |     )
  58 |     await page.getByRole('combobox', { name: 'Template base language' }).selectOption('de')
  59 |     await page.getByRole('button', { name: /create template/i }).click()
  60 | 
  61 |     await expect(page).toHaveURL(/\/en\/templates\/\d+$/)
  62 |     await expect(page.getByRole('heading', { name: templateName })).toBeVisible()
  63 | 
  64 |     await page.getByText('Executive Summary').first().click()
  65 |     await page.getByRole('textbox', { name: 'Section heading' }).fill('Executive Overview')
  66 |     await page.getByRole('button', { name: /save section/i }).click()
  67 |     await page.getByRole('textbox', { name: 'Template version changelog' }).fill(
  68 |       'Renamed executive summary heading.',
  69 |     )
  70 |     await page.getByRole('button', { name: /save version/i }).click()
  71 | 
  72 |     await expect(page.getByText('Executive Overview')).toBeVisible()
  73 |     await page.getByRole('button', { name: 'History' }).click()
  74 |     await expect(page.getByText(/version 2/i)).toBeVisible()
  75 | 
  76 |     expectHealthyClient(errors)
  77 |   })
  78 | 
  79 |   test('unknown templates show an explicit not found state', async ({ page }) => {
  80 |     await page.goto('/en/templates/999999')
> 81 |     await expect(page.getByText(/template 999999 not found/i)).toBeVisible()
     |                                                                ^ Error: expect(locator).toBeVisible() failed
  82 |   })
  83 | })
  84 | 
```