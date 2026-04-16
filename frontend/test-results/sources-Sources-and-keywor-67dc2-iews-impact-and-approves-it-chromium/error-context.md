# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: sources.spec.ts >> Sources and keywords flows >> adds a source, adds keywords, scouts a proposal, previews impact, and approves it
- Location: e2e/sources.spec.ts:36:7

# Error details

```
Error: expect(received).toHaveLength(expected)

Expected length: 0
Received length: 3
Received array:  ["Failed to load resource: the server responded with a status of 500 (Internal Server Error)", "Failed to load resource: the server responded with a status of 500 (Internal Server Error)", "Failed to load resource: the server responded with a status of 500 (Internal Server Error)"]
```

# Page snapshot

```yaml
- generic [ref=e1]:
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
            - img [ref=e88]
            - generic [ref=e90]: Drafts
        - link "Sources" [ref=e91] [cursor=pointer]:
          - /url: /en/clients/gerold-foods/sources
          - generic [ref=e92]:
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
        - link "Sources" [ref=e129] [cursor=pointer]:
          - /url: /en/clients/gerold-foods/sources
          - text: Sources
      - generic [ref=e132]:
        - generic [ref=e133]:
          - generic [ref=e134]:
            - heading "Sources & Keywords" [level=1] [ref=e135]
            - paragraph [ref=e136]: Configure regulatory data sources and keyword matching rules.
          - generic [ref=e137]:
            - button "Sources 12" [ref=e138] [cursor=pointer]:
              - img [ref=e139]
              - text: Sources
              - generic [ref=e145]: "12"
            - button "Keywords 7" [ref=e146] [cursor=pointer]:
              - img [ref=e147]
              - text: Keywords
              - generic [ref=e150]: "7"
            - button "Proposals" [ref=e151] [cursor=pointer]:
              - img [ref=e152]
              - text: Proposals
          - generic [ref=e153]:
            - button "Scout sources" [ref=e155] [cursor=pointer]:
              - img [ref=e156]
              - text: Scout sources
            - generic [ref=e158]:
              - generic [ref=e159]: Reviewed (3)
              - generic [ref=e160]:
                - generic [ref=e162]:
                  - generic [ref=e163]:
                    - generic [ref=e164]:
                      - generic [ref=e165]: Stub Regulation Proposal
                      - generic [ref=e166]: Approved
                    - generic [ref=e167]:
                      - generic [ref=e168]: EUR-Lex
                      - generic [ref=e169]: EU
                      - generic [ref=e170]: 82% confidence
                  - button "Preview impact for Stub Regulation Proposal" [ref=e172] [cursor=pointer]:
                    - img [ref=e173]
                - generic [ref=e178]:
                  - generic [ref=e179]:
                    - generic [ref=e180]:
                      - generic [ref=e181]: Stub Regulation Proposal
                      - generic [ref=e182]: Approved
                    - generic [ref=e183]:
                      - generic [ref=e184]: EUR-Lex
                      - generic [ref=e185]: EU
                      - generic [ref=e186]: 82% confidence
                  - button "Preview impact for Stub Regulation Proposal" [ref=e188] [cursor=pointer]:
                    - img [ref=e189]
                - generic [ref=e194]:
                  - generic [ref=e195]:
                    - generic [ref=e196]:
                      - generic [ref=e197]: Stub Regulation Proposal
                      - generic [ref=e198]: Approved
                    - generic [ref=e199]:
                      - generic [ref=e200]: EUR-Lex
                      - generic [ref=e201]: EU
                      - generic [ref=e202]: 82% confidence
                  - button "Preview impact for Stub Regulation Proposal" [ref=e204] [cursor=pointer]:
                    - img [ref=e205]
        - generic [ref=e210]:
          - generic [ref=e211]:
            - img [ref=e212]
            - generic [ref=e215]:
              - generic [ref=e216]: Impact preview
              - generic [ref=e217]: Stub Regulation Proposal
            - button "Close impact preview" [active] [ref=e218] [cursor=pointer]:
              - img [ref=e219]
          - generic [ref=e223]:
            - generic [ref=e224]:
              - generic [ref=e225]:
                - generic [ref=e226]: "4"
                - generic [ref=e227]: Estimated matches
              - generic [ref=e228]:
                - generic [ref=e229]: +16.0%
                - generic [ref=e230]: Coverage change
            - generic [ref=e231]:
              - generic [ref=e232]:
                - img [ref=e233]
                - generic [ref=e235]: Sample matches (3)
              - generic [ref=e236]:
                - generic [ref=e237]:
                  - generic [ref=e238]: EU PPWR — Recycled Content Mandates for Plastic Packaging (2030/2040)
                  - generic [ref=e239]: sections-4 · sections
                - generic [ref=e240]:
                  - generic [ref=e241]: CSRD / ESRS — First Sustainability Report Due June 2026
                  - generic [ref=e242]: sections-2 · sections
                - generic [ref=e243]:
                  - generic [ref=e244]: VerpackG — 2026 Licence Fee Schedule & LUCID Registration
                  - generic [ref=e245]: sections-1 · sections
  - alert [ref=e246]
```

# Test source

```ts
  1  | import { expect, type Page, test } from '@playwright/test'
  2  | 
  3  | const CLIENT_ID = 'gerold-foods'
  4  | const SOURCES_URL = `/en/clients/${CLIENT_ID}/sources`
  5  | 
  6  | function trackClientErrors(page: Page) {
  7  |   const pageErrors: string[] = []
  8  |   const consoleErrors: string[] = []
  9  | 
  10 |   page.on('pageerror', (error) => pageErrors.push(error.message))
  11 |   page.on('console', (message) => {
  12 |     if (message.type() === 'error') {
  13 |       consoleErrors.push(message.text())
  14 |     }
  15 |   })
  16 | 
  17 |   return { pageErrors, consoleErrors }
  18 | }
  19 | 
  20 | function expectHealthyClient(errors: { pageErrors: string[]; consoleErrors: string[] }) {
  21 |   const fatalPageErrors = errors.pageErrors.filter(
  22 |     (message) => !message.includes('ResizeObserver') && !message.includes('hydrat'),
  23 |   )
  24 |   const fatalConsoleErrors = errors.consoleErrors.filter(
  25 |     (message) =>
  26 |       !message.includes('404') &&
  27 |       !message.includes('favicon') &&
  28 |       !message.includes('ResizeObserver'),
  29 |   )
  30 | 
  31 |   expect(fatalPageErrors).toHaveLength(0)
> 32 |   expect(fatalConsoleErrors).toHaveLength(0)
     |                              ^ Error: expect(received).toHaveLength(expected)
  33 | }
  34 | 
  35 | test.describe('Sources and keywords flows', () => {
  36 |   test('adds a source, adds keywords, scouts a proposal, previews impact, and approves it', async ({ page }) => {
  37 |     const errors = trackClientErrors(page)
  38 |     const sourceName = `Playwright Source ${Date.now()}`
  39 |     const sourceId = `pw_${Date.now()}`
  40 |     const bundleName = `pw_bundle_${Date.now()}`
  41 |     const bundleLabel = bundleName.replace(/_/g, ' ')
  42 |     const keywordOne = `playwright regulation ${Date.now()}`
  43 |     const keywordTwo = `multilingual packaging ${Date.now()}`
  44 | 
  45 |     await page.goto(SOURCES_URL)
  46 |     await expect(page.getByRole('heading', { name: /sources & keywords/i })).toBeVisible()
  47 | 
  48 |     await page.getByRole('button', { name: /add source/i }).click()
  49 |     await page.getByRole('textbox', { name: 'Source display name' }).fill(sourceName)
  50 |     await page.getByRole('textbox', { name: 'Source ID' }).fill(sourceId)
  51 |     await page.getByRole('textbox', { name: 'Source URL' }).fill('https://eur-lex.europa.eu')
  52 |     await page.getByRole('button', { name: /save source/i }).click()
  53 |     await expect(page.getByText(sourceName)).toBeVisible()
  54 | 
  55 |     page.once('dialog', (dialog) => dialog.accept(bundleName))
  56 |     await page.getByRole('button', { name: /keywords/i }).click()
  57 |     await page.getByRole('button', { name: /new bundle/i }).click()
  58 |     await expect(page.getByText(bundleLabel)).toBeVisible()
  59 | 
  60 |     await page.getByRole('button', { name: /^Add rule$/ }).click()
  61 |     await page.getByRole('textbox', { name: 'Keywords' }).fill(`${keywordOne}, ${keywordTwo}`)
  62 |     await page.getByRole('textbox', { name: 'Keyword topics' }).fill('testing')
  63 |     await page.getByRole('textbox', { name: 'Keyword jurisdictions' }).fill('en')
  64 |     await page.locator('button').filter({ hasText: /^Add rule$/ }).last().click()
  65 |     await expect(page.getByText(keywordOne)).toBeVisible()
  66 | 
  67 |     await page.getByRole('button', { name: /proposals/i }).click()
  68 |     await page.getByRole('button', { name: /scout sources/i }).click()
  69 |     await expect(page.getByText(/Stub Regulation Proposal/i).first()).toBeVisible()
  70 | 
  71 |     await page.getByRole('button', { name: /Preview impact for Stub Regulation Proposal/i }).first().click()
  72 |     await expect(page.getByText(/Impact preview/i)).toBeVisible()
  73 |     await page.getByRole('button', { name: /close impact preview/i }).click()
  74 | 
  75 |     const approveButton = page.getByRole('button', { name: /Approve Stub Regulation Proposal/i }).first()
  76 |     if ((await approveButton.count()) > 0) {
  77 |       await approveButton.click()
  78 |     }
  79 |     await expect(page.getByText('Approved', { exact: true }).first()).toBeVisible()
  80 | 
  81 |     expectHealthyClient(errors)
  82 |   })
  83 | })
  84 | 
```