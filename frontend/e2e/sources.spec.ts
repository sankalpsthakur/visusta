import { expect, type Page, test } from '@playwright/test'

const CLIENT_ID = 'gerold-foods'
const SOURCES_URL = `/en/clients/${CLIENT_ID}/sources`

function trackClientErrors(page: Page) {
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

test.describe('Sources and keywords flows', () => {
  test('adds a source, adds keywords, scouts a proposal, previews impact, and approves it', async ({ page }) => {
    const errors = trackClientErrors(page)
    const sourceName = `Playwright Source ${Date.now()}`
    const sourceId = `pw_${Date.now()}`
    const bundleName = `pw_bundle_${Date.now()}`
    const bundleLabel = bundleName.replace(/_/g, ' ')
    const keywordOne = `playwright regulation ${Date.now()}`
    const keywordTwo = `multilingual packaging ${Date.now()}`

    await page.goto(SOURCES_URL)
    await expect(page.getByRole('heading', { name: /sources & keywords/i })).toBeVisible()

    await page.getByRole('button', { name: /add source/i }).click()
    await page.getByRole('textbox', { name: 'Source display name' }).fill(sourceName)
    await page.getByRole('textbox', { name: 'Source ID' }).fill(sourceId)
    await page.getByRole('textbox', { name: 'Source URL' }).fill('https://eur-lex.europa.eu')
    await page.getByRole('button', { name: /save source/i }).click()
    await expect(page.getByText(sourceName)).toBeVisible()

    page.once('dialog', (dialog) => dialog.accept(bundleName))
    await page.getByRole('button', { name: /keywords/i }).click()
    await page.getByRole('button', { name: /new bundle/i }).click()
    await expect(page.getByText(bundleLabel)).toBeVisible()

    await page.getByRole('button', { name: /^Add rule$/ }).click()
    await page.getByRole('textbox', { name: 'Keywords' }).fill(`${keywordOne}, ${keywordTwo}`)
    await page.getByRole('textbox', { name: 'Keyword topics' }).fill('testing')
    await page.getByRole('textbox', { name: 'Keyword jurisdictions' }).fill('en')
    await page.locator('button').filter({ hasText: /^Add rule$/ }).last().click()
    await expect(page.getByText(keywordOne)).toBeVisible()

    await page.getByRole('button', { name: /proposals/i }).click()
    await page.getByRole('button', { name: /scout sources/i }).click()
    await expect(page.getByText(/Stub Regulation Proposal/i).first()).toBeVisible()

    await page.getByRole('button', { name: /Preview impact for Stub Regulation Proposal/i }).first().click()
    await expect(page.getByText(/Impact preview/i)).toBeVisible()
    await page.getByRole('button', { name: /close impact preview/i }).click()

    const approveButton = page.getByRole('button', { name: /Approve Stub Regulation Proposal/i }).first()
    if ((await approveButton.count()) > 0) {
      await approveButton.click()
    }
    await expect(page.getByText('Approved', { exact: true }).first()).toBeVisible()

    expectHealthyClient(errors)
  })
})
