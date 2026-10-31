import { expect, test } from '@playwright/test';

for (const width of [375, 768, 1280]) {
	test(`welcome is usable at ${width}px`, async ({ page }, testInfo) => {
		const errors = [];
		page.on('pageerror', (error) => errors.push(error.message));
		await page.setViewportSize({ width, height: 900 });
		await page.goto('/');
		await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
		await expect(page.getByRole('link', { name: 'Open your workspace' })).toBeVisible();
		await page.evaluate(() => document.fonts.ready);
		expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
			true
		);
		await page.screenshot({
			path: testInfo.outputPath(`welcome-${width}.png`),
			fullPage: true,
			animations: 'disabled'
		});
		expect(errors).toEqual([]);
	});
}

test('private workspace redirects anonymous visitors to login', async ({ page }) => {
	await page.goto('/app/invoices');
	await expect(page).toHaveURL(/\/login\?next=/);
	await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible();
});

test('reduced motion leaves the welcome content visible', async ({ page }) => {
	await page.emulateMedia({ reducedMotion: 'reduce' });
	await page.goto('/');
	await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
});
