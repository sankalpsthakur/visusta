# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: drafts.spec.ts >> Draft studio flows >> creates a draft, composes content, translates, chats, approves, and exports
- Location: e2e/drafts.spec.ts:97:7

# Error details

```
Error: expect(page).toHaveURL(expected) failed

Expected pattern: /\/en\/clients\/gerold-foods\/drafts\/\d+$/
Received string:  "http://localhost:3100/en/clients/gerold-foods/drafts"
Timeout: 5000ms

Call log:
  - Expect "toHaveURL" with timeout 5000ms
    8 × unexpected value "http://localhost:3100/en/clients/gerold-foods/drafts"

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - complementary [ref=e2]:
    - button "Collapse sidebar" [ref=e3]:
      - img [ref=e4]
    - generic [ref=e7]:
      - generic [ref=e8]: V
      - generic [ref=e9]: Visusta
    - button "G Gerold & Team" [ref=e11]:
      - generic [ref=e12]: G
      - generic [ref=e13]: Gerold & Team
      - img [ref=e14]
    - navigation [ref=e16]:
      - generic [ref=e17]:
        - link "Overview" [ref=e18] [cursor=pointer]:
          - /url: /en
          - generic [ref=e19]:
            - img [ref=e21]
            - generic [ref=e24]: Overview
        - link "Clients" [ref=e25] [cursor=pointer]:
          - /url: /en/clients
          - generic [ref=e26]:
            - img [ref=e29]
            - generic [ref=e34]: Clients
        - link "Templates" [ref=e35] [cursor=pointer]:
          - /url: /en/templates
          - generic [ref=e36]:
            - img [ref=e38]
            - generic [ref=e42]: Templates
      - generic [ref=e44]: Gerold & Team
      - generic [ref=e45]:
        - link "Dashboard" [ref=e46] [cursor=pointer]:
          - /url: /en/clients/gerold-foods
          - generic [ref=e47]:
            - img [ref=e50]
            - generic [ref=e55]: Dashboard
        - link "Regulatory" [ref=e56] [cursor=pointer]:
          - /url: /en/clients/gerold-foods/regulatory
          - generic [ref=e57]:
            - img [ref=e59]
            - generic [ref=e63]: Regulatory
        - link "Reports" [ref=e64] [cursor=pointer]:
          - /url: /en/clients/gerold-foods/reports
          - generic [ref=e65]:
            - img [ref=e67]
            - generic [ref=e70]: Reports
        - link "Audit" [ref=e71] [cursor=pointer]:
          - /url: /en/clients/gerold-foods/audit
          - generic [ref=e72]:
            - img [ref=e74]
            - generic [ref=e77]: Audit
        - link "Settings" [ref=e78] [cursor=pointer]:
          - /url: /en/clients/gerold-foods/settings
          - generic [ref=e79]:
            - img [ref=e81]
            - generic [ref=e84]: Settings
        - link "Drafts" [ref=e85] [cursor=pointer]:
          - /url: /en/clients/gerold-foods/drafts
          - generic [ref=e86]:
            - img [ref=e89]
            - generic [ref=e91]: Drafts
        - link "Sources" [ref=e92] [cursor=pointer]:
          - /url: /en/clients/gerold-foods/sources
          - generic [ref=e93]:
            - img [ref=e95]
            - generic [ref=e101]: Sources
    - generic [ref=e104]: System operational
    - generic [ref=e106]:
      - img [ref=e107]
      - combobox "Select language" [ref=e110] [cursor=pointer]:
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
  - main [ref=e111]:
    - generic [ref=e112]:
      - generic [ref=e113]:
        - generic [ref=e114]:
          - link "Clients" [ref=e115] [cursor=pointer]:
            - /url: /en/clients
          - generic [ref=e116]: /
          - generic [ref=e117]: Gerold & Team
        - generic [ref=e118]:
          - generic [ref=e119]: EU
          - generic [ref=e120]: DE
      - generic [ref=e121]:
        - link "Dashboard" [ref=e122] [cursor=pointer]:
          - /url: /en/clients/gerold-foods
        - link "Regulatory" [ref=e123] [cursor=pointer]:
          - /url: /en/clients/gerold-foods/regulatory
        - link "Evidence" [ref=e124] [cursor=pointer]:
          - /url: /en/clients/gerold-foods/evidence
        - link "Reports" [ref=e125] [cursor=pointer]:
          - /url: /en/clients/gerold-foods/reports
        - link "Audit" [ref=e126] [cursor=pointer]:
          - /url: /en/clients/gerold-foods/audit
        - link "Settings" [ref=e127] [cursor=pointer]:
          - /url: /en/clients/gerold-foods/settings
        - link "Drafts" [ref=e128] [cursor=pointer]:
          - /url: /en/clients/gerold-foods/drafts
          - text: Drafts
        - link "Sources" [ref=e130] [cursor=pointer]:
          - /url: /en/clients/gerold-foods/sources
      - img [ref=e134]
  - alert [ref=e136]
```

# Test source

```ts
  1   | import { expect, type APIRequestContext, type Page, test } from '@playwright/test'
  2   | 
  3   | const CLIENT_ID = 'gerold-foods'
  4   | const DRAFTS_URL = `/en/clients/${CLIENT_ID}/drafts`
  5   | const API_BASE_URL = 'http://localhost:8010'
  6   | 
  7   | function trackClientErrors(page: Page) {
  8   |   const pageErrors: string[] = []
  9   |   const consoleErrors: string[] = []
  10  | 
  11  |   page.on('pageerror', (error) => pageErrors.push(error.message))
  12  |   page.on('console', (message) => {
  13  |     if (message.type() === 'error') {
  14  |       consoleErrors.push(message.text())
  15  |     }
  16  |   })
  17  | 
  18  |   return { pageErrors, consoleErrors }
  19  | }
  20  | 
  21  | function expectHealthyClient(errors: { pageErrors: string[]; consoleErrors: string[] }) {
  22  |   const fatalPageErrors = errors.pageErrors.filter(
  23  |     (message) => !message.includes('ResizeObserver') && !message.includes('hydrat'),
  24  |   )
  25  |   const fatalConsoleErrors = errors.consoleErrors.filter(
  26  |     (message) =>
  27  |       !message.includes('404') &&
  28  |       !message.includes('favicon') &&
  29  |       !message.includes('ResizeObserver'),
  30  |   )
  31  | 
  32  |   expect(fatalPageErrors).toHaveLength(0)
  33  |   expect(fatalConsoleErrors).toHaveLength(0)
  34  | }
  35  | 
  36  | async function ensureTemplate(request: APIRequestContext) {
  37  |   const templateName = `Draft Flow Template ${Date.now()}`
  38  |   const templateResponse = await request.post(`${API_BASE_URL}/api/templates`, {
  39  |     data: {
  40  |       name: templateName,
  41  |       description: 'Template created by Playwright for the draft end-to-end flow.',
  42  |       base_locale: 'en',
  43  |     },
  44  |   })
  45  |   expect(templateResponse.ok()).toBeTruthy()
  46  |   const template = await templateResponse.json()
  47  | 
  48  |   const versionResponse = await request.post(`${API_BASE_URL}/api/templates/${template.id}/versions`, {
  49  |     data: {
  50  |       sections_json: [
  51  |         {
  52  |           section_id: 'executive_summary',
  53  |           heading: 'Executive Summary',
  54  |           order: 0,
  55  |           prompt_template: 'Summarize the reporting period.',
  56  |           chart_types: [],
  57  |           max_tokens: 900,
  58  |           required: true,
  59  |         },
  60  |         {
  61  |           section_id: 'critical_actions',
  62  |           heading: 'Critical Actions',
  63  |           order: 1,
  64  |           prompt_template: 'List the urgent follow-up actions and deadlines.',
  65  |           chart_types: [],
  66  |           max_tokens: 700,
  67  |           required: true,
  68  |         },
  69  |       ],
  70  |       theme_tokens: {
  71  |         '--brand-primary': '#10243f',
  72  |         '--brand-accent': '#1d6fd8',
  73  |       },
  74  |       changelog_note: 'Initial Playwright template version',
  75  |       created_by: 'playwright',
  76  |     },
  77  |   })
  78  |   expect(versionResponse.ok()).toBeTruthy()
  79  | 
  80  |   return { templateId: String(template.id), templateName }
  81  | }
  82  | 
  83  | async function createDraft(page: Page, title: string, templateName: string) {
  84  |   await page.goto(DRAFTS_URL)
  85  |   await page.getByRole('button', { name: /new draft/i }).click()
  86  | 
  87  |   await page.getByRole('textbox', { name: 'Draft title' }).fill(title)
  88  |   await page.getByRole('combobox', { name: 'Draft template' }).selectOption({ label: templateName })
  89  |   await page.getByRole('textbox', { name: 'Draft period' }).fill('2026-02')
  90  |   await page.getByRole('combobox', { name: 'Draft language' }).selectOption('en')
  91  |   await page.getByRole('button', { name: /create draft/i }).click()
  92  | 
> 93  |   await expect(page).toHaveURL(/\/en\/clients\/gerold-foods\/drafts\/\d+$/)
      |                      ^ Error: expect(page).toHaveURL(expected) failed
  94  | }
  95  | 
  96  | test.describe('Draft studio flows', () => {
  97  |   test('creates a draft, composes content, translates, chats, approves, and exports', async ({ page, request }) => {
  98  |     const title = `Playwright Draft ${Date.now()}`
  99  |     const errors = trackClientErrors(page)
  100 |     const { templateName } = await ensureTemplate(request)
  101 | 
  102 |     await createDraft(page, title, templateName)
  103 | 
  104 |     await expect(page.getByRole('heading', { name: title })).toBeVisible()
  105 |     await expect(page.getByRole('heading', { name: 'Executive Summary' })).toBeVisible()
  106 |     await expect(page.getByText('Stub executive summary.')).toBeVisible()
  107 | 
  108 |     await page.getByRole('combobox', { name: 'Target translation language' }).selectOption('de')
  109 |     await page.getByRole('button', { name: 'Translate' }).click()
  110 |     await expect(page.getByText(/DE.*Rev 2/)).toBeVisible()
  111 | 
  112 |     const chatBox = page.getByPlaceholder(/Ask the AI/i)
  113 |     await chatBox.fill('Tighten the executive summary and make it more action-oriented.')
  114 |     await chatBox.press('Control+Enter')
  115 |     await expect(page.getByText('Applied requested changes.')).toBeVisible()
  116 | 
  117 |     await page.getByRole('button', { name: 'History' }).click()
  118 |     await expect(page.getByText(/Rev 3/)).toBeVisible()
  119 | 
  120 |     const [docxDownload] = await Promise.all([
  121 |       page.waitForEvent('download', { timeout: 20_000 }),
  122 |       (async () => {
  123 |         await page.getByRole('button', { name: 'Export', exact: true }).click()
  124 |         await page.getByRole('button', { name: /word/i }).click()
  125 |       })(),
  126 |     ])
  127 |     expect(docxDownload.suggestedFilename()).toMatch(/\.docx$/)
  128 | 
  129 |     await page.getByRole('button', { name: /submit for review/i }).click()
  130 |     await page.getByRole('button', { name: /submit for approval/i }).click()
  131 |     await expect(page.getByText(/section approval/i)).toBeVisible()
  132 | 
  133 |     for (const sectionName of ['Executive Summary', 'Critical Actions']) {
  134 |       await page.getByText(sectionName).first().click()
  135 |       await page.getByRole('button', { name: 'Approve' }).click()
  136 |     }
  137 | 
  138 |     await expect(page.getByText('Approved', { exact: true }).first()).toBeVisible()
  139 | 
  140 |     const [pdfDownload] = await Promise.all([
  141 |       page.waitForEvent('download', { timeout: 20_000 }),
  142 |       (async () => {
  143 |         await page.getByRole('button', { name: 'Export', exact: true }).click()
  144 |         await page.getByRole('button', { name: /PDF.*Print-ready document/i }).click()
  145 |       })(),
  146 |     ])
  147 |     expect(pdfDownload.suggestedFilename()).toMatch(/\.pdf$/)
  148 | 
  149 |     expectHealthyClient(errors)
  150 |   })
  151 | 
  152 |   test('unknown drafts show an explicit not found state', async ({ page }) => {
  153 |     await page.goto(`/en/clients/${CLIENT_ID}/drafts/999999`)
  154 |     await expect(page.getByText(/draft 999999 not found/i)).toBeVisible()
  155 |   })
  156 | })
  157 | 
```