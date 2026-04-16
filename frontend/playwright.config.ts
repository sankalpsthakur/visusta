import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:3100',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      command: 'python3 -m uvicorn api.main:app --port 8010',
      cwd: '..',
      url: 'http://localhost:8010/api/health',
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      command: 'NEXT_PUBLIC_API_URL=http://localhost:8010 npm run build && NEXT_PUBLIC_API_URL=http://localhost:8010 npm run start -- --port 3100',
      url: 'http://localhost:3100',
      reuseExistingServer: false,
      timeout: 240_000,
    },
  ],
})
