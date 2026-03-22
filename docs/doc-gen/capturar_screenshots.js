/**
 * Captura screenshots reais do sistema rodando em localhost:4000
 * Saída: docs/screenshots/{login,portal,dashboard,api_docs}.png
 */
const { chromium } = require(require.resolve('@playwright/test', {
  paths: [
    require('path').resolve(__dirname, '../../frontend/node_modules'),
    require('path').resolve(__dirname, '../../frontend'),
  ],
}));
const path = require('path');
const fs = require('fs');

const BASE_URL = 'http://localhost:4000';
const API_URL = 'http://localhost:8000';
const OUT_DIR = path.resolve(__dirname, '..', 'screenshots');

fs.mkdirSync(OUT_DIR, { recursive: true });

async function capture() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    deviceScaleFactor: 1.5,
  });

  // 1. Login
  const loginPage = await context.newPage();
  console.log('📸 Capturando tela de Login...');
  await loginPage.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle', timeout: 30000 });
  await loginPage.screenshot({ path: path.join(OUT_DIR, 'login.png'), fullPage: false });
  console.log('   ✓ login.png');

  // 2. Fazer login para acessar áreas autenticadas
  let loggedIn = false;
  try {
    await loginPage.fill('input[name="email"], input[type="email"]', 'admin@hw1.com.br');
    await loginPage.fill('input[name="password"], input[type="password"]', 'Admin@2026');
    await loginPage.click('button[type="submit"]');
    await loginPage.waitForURL(/dashboard|portal/, { timeout: 10000 });
    loggedIn = true;
    console.log('   ✓ Login realizado');
  } catch (e) {
    console.log(`   ⚠ Login automático falhou: ${e.message.split('\n')[0]}`);
  }

  // 3. Dashboard
  if (loggedIn) {
    const dashPage = await context.newPage();
    console.log('📸 Capturando Dashboard...');
    try {
      await dashPage.goto(`${BASE_URL}/dashboard`, { waitUntil: 'networkidle', timeout: 20000 });
      await dashPage.screenshot({ path: path.join(OUT_DIR, 'dashboard.png'), fullPage: false });
      console.log('   ✓ dashboard.png');
    } catch (e) {
      // mesmo sem login, captura o que tiver
      await dashPage.screenshot({ path: path.join(OUT_DIR, 'dashboard.png') });
      console.log('   ⚠ dashboard.png (sem login)');
    }
    await dashPage.close();

    // 4. Portal do cliente
    const portalPage = await context.newPage();
    console.log('📸 Capturando Portal do Cliente...');
    try {
      await portalPage.goto(`${BASE_URL}/portal`, { waitUntil: 'networkidle', timeout: 20000 });
      await portalPage.screenshot({ path: path.join(OUT_DIR, 'portal.png'), fullPage: false });
      console.log('   ✓ portal.png');
    } catch (e) {
      await portalPage.screenshot({ path: path.join(OUT_DIR, 'portal.png') });
      console.log('   ⚠ portal.png (fallback)');
    }
    await portalPage.close();
  } else {
    // Sem login: captura as telas públicas/redireciona
    const dashPage = await context.newPage();
    await dashPage.goto(`${BASE_URL}/dashboard`, { waitUntil: 'domcontentloaded', timeout: 15000 }).catch(() => {});
    await dashPage.screenshot({ path: path.join(OUT_DIR, 'dashboard.png') });
    await dashPage.close();

    const portalPage = await context.newPage();
    await portalPage.goto(`${BASE_URL}/portal`, { waitUntil: 'domcontentloaded', timeout: 15000 }).catch(() => {});
    await portalPage.screenshot({ path: path.join(OUT_DIR, 'portal.png') });
    await portalPage.close();
  }

  // 5. Swagger / API Docs
  const swaggerPage = await context.newPage();
  console.log('📸 Capturando Swagger / API Docs...');
  try {
    await swaggerPage.goto(`${API_URL}/docs`, { waitUntil: 'networkidle', timeout: 20000 });
    // aguarda o Swagger UI renderizar
    await swaggerPage.waitForSelector('.swagger-ui', { timeout: 10000 }).catch(() => {});
    await swaggerPage.screenshot({ path: path.join(OUT_DIR, 'api_docs.png'), fullPage: false });
    console.log('   ✓ api_docs.png');
  } catch (e) {
    console.log(`   ⚠ api_docs.png: ${e.message.split('\n')[0]}`);
    await swaggerPage.screenshot({ path: path.join(OUT_DIR, 'api_docs.png') });
  }
  await swaggerPage.close();

  await loginPage.close();
  await browser.close();

  console.log('\n✅ Screenshots salvos em:', OUT_DIR);
  const files = fs.readdirSync(OUT_DIR).filter(f => f.endsWith('.png'));
  files.forEach(f => {
    const size = fs.statSync(path.join(OUT_DIR, f)).size;
    console.log(`   ${f}: ${(size / 1024).toFixed(0)} KB`);
  });
}

capture().catch(e => {
  console.error('ERRO:', e.message);
  process.exit(1);
});
