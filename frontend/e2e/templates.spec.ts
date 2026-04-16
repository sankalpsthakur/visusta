import { expect, test } from '@playwright/test'

function trackClientErrors(page: import('@playwright/test').Page) {
  const pageErrors: string[] = []
  const consoleErrors: string[] = []

  page.on('pageerror', (error) => pageErrors.push(error.message))
  page.on('console', (message) => {
    if (message.type() === 'error') {
      consoleErrors.push(message.text())
    }
  })

  return { pageErrors, consoleErrors }
}

function expectHealthyClient(errors: { pageErrors: string[]; consoleErrors: string[] }) {
  const fatalPageErrors = errors.pageErrors.filter(
    (message) => !message.includes('ResizeObserver') && !message.includes('hydrat'),
  )
  const fatalConsoleErrors = errors.consoleErrors.filter(
    (message) =>
      !message.includes('404') &&
      !message.includes('favicon') &&
      !message.includes('ResizeObserver'),
  )

  expect(fatalPageErrors).toHaveLength(0)
  expect(fatalConsoleErrors).toHaveLength(0)
}

test.describe('Templates flows', () => {
  test('list view renders without overlays or client errors', async ({ page }) => {
    const errors = trackClientErrors(page)

    const response = await page.goto('/en/templates')
    expect(response?.status()).toBe(200)

    await expect(page.getByRole('heading', { name: 'Templates' })).toBeVisible()
    await expect(page.getByRole('button', { name: /new template/i })).toBeVisible()
    await expect(page.getByText(/failed to load templates/i)).toHaveCount(0)
    await expect(page.getByText(/This page couldn’t load/i)).toHaveCount(0)

    expectHealthyClient(errors)
  })

  test('creates a template and saves a new version through the editor', async ({ page }) => {
    const templateName = `Playwright Template ${Date.now()}`
    const errors = trackClientErrors(page)

    await page.goto('/en/templates')
    await page.getByRole('button', { name: /new template/i }).click()

    await page.getByRole('textbox', { name: 'Template name' }).fill(templateName)
    await page.getByRole('textbox', { name: 'Template description' }).fill(
      'Quarterly cross-border compliance reporting for adversarial browser verification.',
    )
    await page.getByRole('combobox', { name: 'Template base language' }).selectOption('de')
    await page.getByRole('button', { name: /create template/i }).click()

    await expect(page).toHaveURL(/\/en\/templates\/\d+$/)
    await expect(page.getByRole('heading', { name: templateName })).toBeVisible()

    await page.getByText('Executive Summary').first().click()
    await page.getByRole('textbox', { name: 'Section heading' }).fill('Executive Overview')
    await page.getByRole('button', { name: /save section/i }).click()
    await page.getByRole('textbox', { name: 'Template version changelog' }).fill(
      'Renamed executive summary heading.',
    )
    await page.getByRole('button', { name: /save version/i }).click()

    await expect(page.getByText('Executive Overview')).toBeVisible()
    await page.getByRole('button', { name: 'History' }).click()
    await expect(page.getByText(/version 2/i)).toBeVisible()

    expectHealthyClient(errors)
  })

  test('unknown templates show an explicit not found state', async ({ page }) => {
    await page.goto('/en/templates/999999')
    await expect(page.getByText(/template 999999 not found/i)).toBeVisible()
  })
})
