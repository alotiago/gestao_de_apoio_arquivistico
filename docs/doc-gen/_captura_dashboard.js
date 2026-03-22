// Captura screenshot do dashboard após login
const path = require('path');
const { chromium } = require(require.resolve('@playwright/test', {
  paths: [path.resolve(__dirname, '../../frontend/node_modules')],
}));

(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1.5 });
  const page = await ctx.newPage();

  await page.goto('http://localhost:4000/login', { waitUntil: 'networkidle', timeout: 120000 });
  await page.fill('input[type="email"]', 'admin@hw1.com.br');
  await page.fill('input[type="password"]', 'Admin@2026');
  await page.click('button[type="submit"]');
  await page.waitForURL(/dashboard/, { timeout: 60000 });
  // aguarda painel carregar dados
  await page.waitForTimeout(3000);

  const out = path.resolve(__dirname, '../screenshots/dashboard.png');
  await page.screenshot({ path: out, fullPage: false });
  console.log('OK:', out);
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });
