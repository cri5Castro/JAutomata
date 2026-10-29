import { defineConfig, devices } from '@playwright/test';

const localBaseURL = 'http://127.0.0.1:4321/JAutomata/';
const externalBaseURL = process.env.PLAYWRIGHT_BASE_URL;
const baseURL = (externalBaseURL ?? localBaseURL).endsWith('/')
  ? externalBaseURL ?? localBaseURL
  : `${externalBaseURL}/`;

export default defineConfig({
  testDir: './tests',
  testMatch: '**/*.spec.ts',
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['list'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'desktop-chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile-chromium', use: { ...devices['Pixel 5'] } },
  ],
  webServer: externalBaseURL
    ? undefined
    : {
        command: 'npm run preview -- --port 4321',
        url: localBaseURL,
        timeout: 120_000,
        reuseExistingServer: !process.env.CI,
        stdout: 'ignore',
        stderr: 'pipe',
      },
});
