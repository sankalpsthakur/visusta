import { expect, test } from '@playwright/test'

test.describe('Locale routing', () => {
  test('supports EU locale routes beyond the original seven', async ({ page }) => {
    const response = await page.goto('/pl/templates')
    expect(response?.status()).toBe(200)
    await expect(page.locator('html')).toHaveAttribute('lang', 'pl')
    await expect(page.getByRole('button', { name: /new template/i })).toBeVisible()
  })

  test('switching locale preserves the current path', async ({ page }) => {
    await page.goto('/en/templates')
    await page.getByLabel('Select language').selectOption('de')
    await expect(page).toHaveURL(/\/de\/templates$/)
    await page.getByLabel('Select language').selectOption('fr')
    await expect(page).toHaveURL(/\/fr\/templates$/)
  })

  test('invalid locales return the Next not found page', async ({ page }) => {
    const response = await page.goto('/xx/templates')
    expect(response?.status()).toBe(404)
    await expect(page.getByText(/This page could not be found/i)).toBeVisible()
  })
})
