import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

const route = (path = '') => `./${path}`;

function rectanglesOverlap(
  first: { x: number; y: number; width: number; height: number },
  second: { x: number; y: number; width: number; height: number },
) {
  return first.x < second.x + second.width && first.x + first.width > second.x
    && first.y < second.y + second.height && first.y + first.height > second.y;
}

test('landing page presents the learning path and keyboard-visible navigation', async ({ page }) => {
  await page.goto(route());
  await expect(page.getByRole('heading', { name: 'Make every state visible.' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Skip to content' })).toBeVisible();
  await page.keyboard.press('Tab');
  await expect(page.locator(':focus')).toHaveAttribute('href', '#_top');
});

test('lesson keeps diagram alternatives, focus controls, and generated trace state usable', async ({ page }, testInfo) => {
  await page.goto(route('learn/thompson/'));
  await expect(page.getByRole('heading', { name: /thompson/i }).first()).toBeVisible();
  const diagrams = page.locator('img.diagram');
  expect(await diagrams.count()).toBeGreaterThan(0);
  for (let index = 0; index < await diagrams.count(); index += 1) {
    await expect(diagrams.nth(index)).toHaveAttribute('alt', /.+/);
  }

  const focus = page.locator('[data-focus-bar]');
  const focusButton = focus.getByRole('button');
  await focusButton.click();
  await expect(focusButton).toHaveAttribute('aria-pressed', 'true');
  await expect(focusButton).toHaveText('Exit focus view');
  const toc = page.getByRole('heading', { name: 'On this page' });
  if (await toc.count()) {
    const [focusBox, tocBox] = await Promise.all([focus.boundingBox(), toc.first().boundingBox()]);
    expect(focusBox).not.toBeNull();
    expect(tocBox).not.toBeNull();
    expect(rectanglesOverlap(focusBox!, tocBox!)).toBeFalsy();
  }
  await focusButton.click();
  await expect(focusButton).toHaveAttribute('aria-pressed', 'false');

  const player = page.locator('[data-trace]').first();
  const trace = JSON.parse(await player.getAttribute('data-trace') ?? '{}');
  await expect(player.getByText(`Step 1 of ${trace.steps.length}`)).toBeVisible();
  await player.getByRole('button', { name: 'Next step' }).click();
  await expect(player.getByText(`Step 2 of ${trace.steps.length}`)).toBeVisible();
  await expect(player.locator('[data-consumed]')).toHaveText(trace.steps[1].consumed || 'nothing yet');

  const scan = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();
  await testInfo.attach('axe-thompson', { body: JSON.stringify(scan, null, 2), contentType: 'application/json' });
  expect(scan.violations).toEqual([]);
});

test('generated API reference and Pagefind search navigate within the deployed base path', async ({ page }) => {
  await page.goto(route('python-api/'));
  await expect(page.getByRole('heading', { name: /python api/i }).first()).toBeVisible();
  await expect(page.locator('a[href*="github.com/cri5Castro/JAutomata/blob/master/python/"]').first()).toBeVisible();

  const search = page.locator('#starlight__search input').first();
  await expect(search).toBeAttached({ timeout: 15_000 });
  await page.getByRole('button', { name: /search/i }).first().click();
  await expect(search).toBeVisible();
  await search.fill('Thompson construction');
  const result = page.getByRole('dialog', { name: 'Search' })
    .getByRole('link', { name: /thompson construction/i }).first();
  await expect(result).toBeVisible({ timeout: 15_000 });
  await result.click();
  await expect(page).toHaveURL(/\/JAutomata\/learn\/thompson\//);
});

test('mobile controls remain in document flow and reduced motion is honored', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto(route('learn/thompson/'));
  const focus = page.locator('[data-focus-bar]');
  await expect(focus).toBeVisible();
  const mobileToc = page.getByRole('button', { name: /on this page/i });
  if (await mobileToc.count()) {
    const [focusBox, tocBox] = await Promise.all([focus.boundingBox(), mobileToc.first().boundingBox()]);
    expect(focusBox).not.toBeNull();
    expect(tocBox).not.toBeNull();
    expect(rectanglesOverlap(focusBox!, tocBox!)).toBeFalsy();
  }
  const transitionDuration = await focus.evaluate((element) => getComputedStyle(element).transitionDuration);
  expect(Number.parseFloat(transitionDuration)).toBeLessThanOrEqual(0.01);
});

test('light and dark schemes have no automatically detectable WCAG A/AA violations', async ({ page }, testInfo) => {
  for (const colorScheme of ['light', 'dark'] as const) {
    await page.emulateMedia({ colorScheme });
    await page.goto(route());
    const scan = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
      .analyze();
    await testInfo.attach(`axe-${colorScheme}`, { body: JSON.stringify(scan, null, 2), contentType: 'application/json' });
    expect(scan.violations).toEqual([]);
  }
});

test('search name remains accessible across platform shortcut and viewport changes', async ({ browser, baseURL }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-chromium', 'The visible shortcut is desktop-only.');
  const platforms = [
    ['Linux x86_64', 'Search Ctrl K'],
    ['Win32', 'Search Ctrl K'],
    ['MacIntel', 'Search ⌘ K'],
  ] as const;

  for (const [platform, expectedName] of platforms) {
    const context = await browser.newContext({ viewport: { width: 700, height: 900 } });
    await context.addInitScript((value) => {
      Object.defineProperty(navigator, 'platform', { configurable: true, value });
    }, platform);
    const page = await context.newPage();
    await page.goto(new URL('', baseURL).toString());
    const control = page.locator('button[data-open-modal]');
    for (const [width, renderedName] of [[700, ''], [1000, expectedName], [700, '']] as const) {
      await page.setViewportSize({ width, height: 900 });
      await page.waitForTimeout(50);
      await expect(control).toHaveAttribute('aria-label', expectedName);
      expect(await control.evaluate((element) => (element.textContent ?? '').replace(/\s+/g, ' ').trim())).toBe(expectedName);
      expect(await control.evaluate((element) => (element as HTMLButtonElement).innerText.replace(/\s+/g, ' ').trim())).toBe(renderedName);
      const scan = await new AxeBuilder({ page })
        .include('button[data-open-modal]')
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
        .analyze();
      expect(scan.violations).toEqual([]);
    }
    await context.close();
  }
});

test('learning map leads to paired study and dense curriculum pages stay usable', async ({ page }, testInfo) => {
  await page.goto(route('learning-map/'));
  const main = page.locator('main');
  await expect(main.getByRole('heading', { name: 'Complete learning map' })).toHaveCount(1);
  await expect(main.getByRole('heading', { name: 'Complete learning map' })).toBeVisible();
  await expect(main.locator('#complete-learning-map')).toHaveCount(1);
  await main.getByRole('link', { name: 'Finite automata and languages' }).click();
  await expect(page).toHaveURL(/\/JAutomata\/theory\/automata\//);
  await page.locator('main').getByRole('link', { name: 'paired tutorial' }).click();
  await expect(page).toHaveURL(/\/JAutomata\/tutorials\/automata\//);

  await page.goto(route('learning-map/'));
  await main.getByRole('link', { name: /Practica 3:/ }).click();
  await expect(page).toHaveURL(/\/JAutomata\/labs\/practica3\//);

  await page.goto(route('tutorials/validation-complexity/'));
  const details = main.locator('details').first();
  const summary = details.locator('summary');
  await summary.focus();
  await page.keyboard.press('Enter');
  await expect(details).toHaveAttribute('open', '');
  const code = page.locator('.expressive-code pre').first();
  await expect(code).toBeVisible();
  await code.focus();
  await expect(page.locator(':focus')).toHaveAttribute('aria-label', 'Scrollable code example');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  const scan = await new AxeBuilder({ page }).include('main').analyze();
  await testInfo.attach('axe-dense-curriculum-page', { body: JSON.stringify(scan, null, 2), contentType: 'application/json' });
  expect(scan.violations).toEqual([]);
});

test('essential lesson text and diagram alternatives remain available without JavaScript', async ({ browser, baseURL }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto(new URL('learn/thompson/', baseURL).toString());
  await expect(page.getByRole('heading', { name: /thompson/i }).first()).toBeVisible();
  await expect(page.locator('img.diagram').first()).toHaveAttribute('alt', /.+/);
  await expect(page.getByText(/Without JavaScript:/)).toBeVisible();
  await context.close();
});

test('learning map and a capstone remain navigable without JavaScript', async ({ browser, baseURL }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto(new URL('learning-map/', baseURL).toString());
  await expect(page.getByRole('heading', { name: 'Complete learning map' })).toHaveCount(1);
  await expect(page.getByRole('heading', { name: 'Complete learning map' })).toBeVisible();
  await expect(page.locator('#complete-learning-map')).toHaveCount(1);
  await expect(page.getByRole('link', { name: /Practica 3:/ }).first()).toBeVisible();
  await page.goto(new URL('labs/main/', baseURL).toString());
  await expect(page.getByRole('heading', { name: /Main: turn historical experiments/i }).first()).toBeVisible();
  await context.close();
});
