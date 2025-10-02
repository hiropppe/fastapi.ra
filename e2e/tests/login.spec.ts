import { test, expect } from '@playwright/test';

test('login page', async ({page}) => {
  await page.goto('http://192.168.88.214:5173/#/login');
  await expect(page).toHaveTitle(/Dnet.ra/);
  await page.fill('input[name="username"]', 'take');
  await page.fill('input[name="password"]', 'taKe.910');
  await page.getByRole('button', { name: 'ログイン' }).click();
  // await page.getByText('ログイン').click();
  await expect(page.locator('#main-content')).toBeVisible();
});

