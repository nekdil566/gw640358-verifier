const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');

const FILE = 'file://' + path.resolve('wind-farm-verifier.html');
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const CSV = path.resolve('sample_farm.csv');
const PDF = path.resolve('sample_farm.pdf');

(async () => {
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: 'new',
    args: ['--no-sandbox', '--allow-file-access-from-files']
  });
  const page = await browser.newPage();
  await page.setCacheEnabled(false);  // avoid stale file:// cache during dev
  const errors = [];
  page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push('CONSOLE: ' + m.text()); });

  await page.goto(FILE, { waitUntil: 'load' });
  // wait for app hook
  await page.waitForFunction('window.__v && typeof window.__v.parseCSV === "function"', { timeout: 10000 });

  // 1) CSV import via the real <input type=file>
  const csvInput = await page.$('#csv');
  await csvInput.uploadFile(CSV);
  await page.evaluate(() => document.getElementById('csv').dispatchEvent(new Event('change')));
  await page.waitForFunction('window.__v.list.length === 4', { timeout: 8000 });
  const csvList = await page.evaluate(() => window.__v.list.map(t => t.id));

  // 2) farm name derived from filename
  const farmAfterCsv = await page.evaluate(() => window.__v.farmName);

  // 3) mark first turbine OK
  await page.evaluate(() => window.__v.markOK(window.__v.list[0].id));
  const firstStatus = await page.evaluate(() => {
    const t = window.__v.list.find(x => x.id === window.__v.list[0].id);
    return { dist: t.dist, status: t.status };
  });

  // 4) simulate a map click correction on the 2nd turbine
  await page.evaluate(() => window.__v.startEdit(window.__v.list[1].id));
  await page.evaluate(() => {
    // emulate a Leaflet map click at a slightly offset coord
    const t = window.__v.list[1];
    window.__v.onMapClick({ latlng: { lat: t.lat + 0.0005, lng: t.lon + 0.0005 } });
  });
  const corrected = await page.evaluate(() => {
    const t = window.__v.list[1];
    return { hasClat: t.clat !== undefined, dist: t.dist };
  });

  // 5) PDF import (fresh load) — verify server-free parsing
  const pdfInput = await page.$('#pdf');
  await pdfInput.uploadFile(PDF);
  await page.evaluate(() => document.getElementById('pdf').dispatchEvent(new Event('change')));
  await page.waitForFunction('window.__v.list.length >= 1', { timeout: 15000 });
  const pdfList = await page.evaluate(() => window.__v.list.map(t => [t.id, t.lat.toFixed(4), t.lon.toFixed(4)]));

  // 6) export produces CSV content
  const exported = await page.evaluate(() => {
    let captured = null;
    const orig = URL.createObjectURL;
    // intercept by overriding anchor click
    const realClick = HTMLAnchorElement.prototype.click;
    HTMLAnchorElement.prototype.click = function(){ captured = this.href; };
    window.__v.exportCSV();
    HTMLAnchorElement.prototype.click = realClick;
    return captured ? 'export-triggered' : 'no-export';
  });

  console.log(JSON.stringify({
    csvRows: csvList,
    farmAfterCsv,
    firstStatus,
    corrected,
    pdfRows: pdfList,
    exported,
    errors
  }, null, 2));

  await browser.close();
  if (errors.length) process.exit(2);
})().catch(e => { console.error('TEST FAILED:', e); process.exit(1); });
