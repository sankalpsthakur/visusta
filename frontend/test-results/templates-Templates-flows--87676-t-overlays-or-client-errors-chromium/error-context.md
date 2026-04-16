# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: templates.spec.ts >> Templates flows >> list view renders without overlays or client errors
- Location: e2e/templates.spec.ts:33:7

# Error details

```
Error: expect(received).toHaveLength(expected)

Expected length: 0
Received length: 16
Received array:  ["Failed to load resource: the server responded with a status of 500 (Internal Server Error)", "Failed to load resource: the server responded with a status of 500 (Internal Server Error)", "Failed to load resource: the server responded with a status of 500 (Internal Server Error)", "Failed to load resource: the server responded with a status of 500 (Internal Server Error)", "Failed to load resource: the server responded with a status of 500 (Internal Server Error)", "Failed to load resource: the server responded with a status of 500 (Internal Server Error)", "Failed to load resource: the server responded with a status of 500 (Internal Server Error)", "Failed to load resource: the server responded with a status of 500 (Internal Server Error)", "Failed to load resource: the server responded with a status of 500 (Internal Server Error)", "Failed to load resource: the server responded with a status of 500 (Internal Server Error)", …]
```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - complementary [ref=e2]:
    - button "Collapse sidebar" [ref=e3]:
      - img [ref=e4]
    - generic [ref=e7]:
      - generic [ref=e8]: V
      - generic: Visusta
    - button "V Select client" [ref=e10]:
      - generic [ref=e11]: V
      - generic [ref=e12]: Select client
      - img [ref=e13]
    - navigation [ref=e15]:
      - generic [ref=e16]:
        - link "Overview" [ref=e17] [cursor=pointer]:
          - /url: /en
          - generic [ref=e18]:
            - img [ref=e20]
            - generic [ref=e23]: Overview
        - link "Clients" [ref=e24] [cursor=pointer]:
          - /url: /en/clients
          - generic [ref=e25]:
            - img [ref=e27]
            - generic [ref=e32]: Clients
        - link "Templates" [ref=e33] [cursor=pointer]:
          - /url: /en/templates
          - generic [ref=e34]:
            - img [ref=e37]
            - generic [ref=e41]: Templates
    - generic [ref=e42]:
      - generic: Backend offline
    - generic [ref=e45]:
      - img [ref=e46]
      - combobox "Select language" [ref=e49] [cursor=pointer]:
        - option "English" [selected]
        - option "Български"
        - option "Čeština"
        - option "Dansk"
        - option "Deutsch"
        - option "Ελληνικά"
        - option "Español"
        - option "Eesti"
        - option "Suomi"
        - option "Français"
        - option "Gaeilge"
        - option "Hrvatski"
        - option "Magyar"
        - option "Italiano"
        - option "Lietuvių"
        - option "Latviešu"
        - option "Malti"
        - option "Nederlands"
        - option "Polski"
        - option "Português"
        - option "Română"
        - option "Slovenčina"
        - option "Slovenščina"
        - option "Svenska"
  - main [ref=e50]:
    - generic [ref=e52]:
      - generic [ref=e53]:
        - generic [ref=e54]:
          - heading "Templates" [level=1] [ref=e55]
          - paragraph [ref=e56]: Manage report structure, prompts, and branding for generated documents.
        - button "New template" [ref=e57] [cursor=pointer]:
          - img [ref=e58]
          - text: New template
      - generic [ref=e59]:
        - generic [ref=e60]:
          - img [ref=e61]
          - textbox "Search templates…" [ref=e64]
        - button "all" [ref=e65] [cursor=pointer]
        - button "monthly" [ref=e66] [cursor=pointer]
        - button "quarterly" [ref=e67] [cursor=pointer]
        - button "custom" [ref=e68] [cursor=pointer]
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
> 29 |   expect(fatalConsoleErrors).toHaveLength(0)
     |                              ^ Error: expect(received).toHaveLength(expected)
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
  81 |     await expect(page.getByText(/template 999999 not found/i)).toBeVisible()
  82 |   })
  83 | })
  84 | 
```