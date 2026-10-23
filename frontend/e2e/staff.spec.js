import { expect, test } from '@playwright/test';
import { PIXEL_PNG, STAFF, login, unique } from './helpers';

test('staff adds an animal with a photo and it shows on the home page', async ({ page }, testInfo) => {
  const name = unique('Biscuit', testInfo);

  await login(page, STAFF);
  await page.getByRole('link', { name: 'Staff panel' }).click();
  await page.getByRole('button', { name: 'Animals' }).click();

  await page.getByRole('button', { name: 'Add animal' }).click();
  const form = page.locator('form.animal-form');
  await form.getByLabel('Name').fill(name);
  await form.getByLabel('Species').fill('Cat');
  await form.getByLabel('Breed').fill('Tabby');
  await form.getByLabel('Age').fill('1');
  await form.getByLabel('Shelter').selectOption({ index: 1 });
  await form.getByRole('button', { name: 'Add animal' }).click();

  const row = page.getByRole('row').filter({ hasText: name });
  await expect(row).toBeVisible();
  await row.getByLabel('Choose photo').setInputFiles({ name: 'cat.png', mimeType: 'image/png', buffer: PIXEL_PNG });
  await row.getByRole('button', { name: 'Upload' }).click();
  await expect(row.getByRole('button', { name: 'Remove' })).toBeVisible();

  await page.getByRole('link', { name: 'Animals', exact: true }).click();
  const photo = page.getByTestId('animal-card').filter({ hasText: name }).getByRole('img', { name: `Photo of ${name}` });
  await expect(photo).toBeVisible();
  // naturalWidth > 0 means the browser really loaded the image from the API.
  await expect.poll(() => photo.evaluate((img) => img.naturalWidth)).toBeGreaterThan(0);
});

test('the register form shows validation errors before calling the API', async ({ page }) => {
  await page.goto('/register');
  await page.getByLabel('Email').fill('not-an-email');
  await page.getByLabel('Password').fill('short');
  await page.getByRole('button', { name: 'Register' }).click();

  await expect(page.getByText('Enter a valid email')).toBeVisible();
  await expect(page.getByText('Password must be at least 8 characters')).toBeVisible();
});
