import { defineConfig } from "@playwright/test";

const reuseServer = process.env.CI ? false : true;

export default defineConfig({
  testDir: "./e2e",
  timeout: 60000,
  use: {
    baseURL: "http://127.0.0.1:8000",
    actionTimeout: 15000,
    navigationTimeout: 30000,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  webServer: {
    command: "pwsh -NoProfile -File ..\\scripts\\run_local.ps1 -NoOpen -NoReload -NoInstall",
    port: 8000,
    reuseExistingServer: reuseServer,
    timeout: 120000,
  },
});
