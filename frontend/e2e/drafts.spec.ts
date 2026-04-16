import { expect, type APIRequestContext, type Page, test } from '@playwright/test'

const CLIENT_ID = 'gerold-foods'
const DRAFTS_URL = `/en/clients/${CLIENT_ID}/drafts`
const API_BASE_URL = 'http://localhost:8010'

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

async function ensureTemplate(request: APIRequestContext) {
  const templateName = `Draft Flow Template ${Date.now()}`
  const templateResponse = await request.post(`${API_BASE_URL}/api/templates`, {
    data: {
      name: templateName,
      description: 'Template created by Playwright for the draft end-to-end flow.',
      base_locale: 'en',
    },
  })
  expect(templateResponse.ok()).toBeTruthy()
  const template = await templateResponse.json()

  const versionResponse = await request.post(`${API_BASE_URL}/api/templates/${template.id}/versions`, {
    data: {
      sections_json: [
        {
          section_id: 'executive_summary',
          heading: 'Executive Summary',
          order: 0,
          prompt_template: 'Summarize the reporting period.',
          chart_types: [],
          max_tokens: 900,
          required: true,
        },
        {
          section_id: 'critical_actions',
          heading: 'Critical Actions',
          order: 1,
          prompt_template: 'List the urgent follow-up actions and deadlines.',
          chart_types: [],
          max_tokens: 700,
          required: true,
        },
      ],
      theme_tokens: {
        '--brand-primary': '#10243f',
        '--brand-accent': '#1d6fd8',
      },
      changelog_note: 'Initial Playwright template version',
      created_by: 'playwright',
    },
  })
  expect(versionResponse.ok()).toBeTruthy()

  return { templateId: String(template.id), templateName }
}

async function createDraft(page: Page, title: string, templateName: string) {
  await page.goto(DRAFTS_URL)
  await page.getByRole('button', { name: /new draft/i }).click()

  await page.getByRole('textbox', { name: 'Draft title' }).fill(title)
  await page.getByRole('combobox', { name: 'Draft template' }).selectOption({ label: templateName })
  await page.getByRole('textbox', { name: 'Draft period' }).fill('2026-02')
  await page.getByRole('combobox', { name: 'Draft language' }).selectOption('en')
  await page.getByRole('button', { name: /create draft/i }).click()

  await expect(page).toHaveURL(/\/en\/clients\/gerold-foods\/drafts\/\d+$/)
}

test.describe('Draft studio flows', () => {
  test('creates a draft, composes content, translates, chats, approves, and exports', async ({ page, request }) => {
    const title = `Playwright Draft ${Date.now()}`
    const errors = trackClientErrors(page)
    const { templateName } = await ensureTemplate(request)

    await createDraft(page, title, templateName)

    await expect(page.getByRole('heading', { name: title })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Executive Summary' })).toBeVisible()
    await expect(page.getByText('Stub executive summary.')).toBeVisible()

    await page.getByRole('combobox', { name: 'Target translation language' }).selectOption('de')
    await page.getByRole('button', { name: 'Translate' }).click()
    await expect(page.getByText(/DE.*Rev 2/)).toBeVisible()

    const chatBox = page.getByPlaceholder(/Ask the AI/i)
    await chatBox.fill('Tighten the executive summary and make it more action-oriented.')
    await chatBox.press('Control+Enter')
    await expect(page.getByText('Applied requested changes.')).toBeVisible()

    await page.getByRole('button', { name: 'History' }).click()
    await expect(page.getByText(/Rev 3/)).toBeVisible()

    const [docxDownload] = await Promise.all([
      page.waitForEvent('download', { timeout: 20_000 }),
      (async () => {
        await page.getByRole('button', { name: 'Export', exact: true }).click()
        await page.getByRole('button', { name: /word/i }).click()
      })(),
    ])
    expect(docxDownload.suggestedFilename()).toMatch(/\.docx$/)

    await page.getByRole('button', { name: /submit for review/i }).click()
    await page.getByRole('button', { name: /submit for approval/i }).click()
    await expect(page.getByText(/section approval/i)).toBeVisible()

    for (const sectionName of ['Executive Summary', 'Critical Actions']) {
      await page.getByText(sectionName).first().click()
      await page.getByRole('button', { name: 'Approve' }).click()
    }

    await expect(page.getByText('Approved', { exact: true }).first()).toBeVisible()

    const [pdfDownload] = await Promise.all([
      page.waitForEvent('download', { timeout: 20_000 }),
      (async () => {
        await page.getByRole('button', { name: 'Export', exact: true }).click()
        await page.getByRole('button', { name: /PDF.*Print-ready document/i }).click()
      })(),
    ])
    expect(pdfDownload.suggestedFilename()).toMatch(/\.pdf$/)

    expectHealthyClient(errors)
  })

  test('unknown drafts show an explicit not found state', async ({ page }) => {
    await page.goto(`/en/clients/${CLIENT_ID}/drafts/999999`)
    await expect(page.getByText(/draft 999999 not found/i)).toBeVisible()
  })
})
