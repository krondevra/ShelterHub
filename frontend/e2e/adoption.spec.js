import { expect, test } from '@playwright/test';
import { STAFF, createAnimal, login, logout, register, unique } from './helpers';

test('an adopter applies, staff approves, and the adopter sees the result', async ({ page, request }, testInfo) => {
  const animal = await createAnimal(request, unique('Rex', testInfo));
  const adopter = `${unique('adopter', testInfo)}@example.com`;

  await register(page, adopter);
  await login(page, adopter);

  const card = page.getByTestId('animal-card').filter({ hasText: animal.name });
  await card.getByRole('button', { name: 'Apply to adopt' }).click();
  await expect(card.getByText('Application submitted')).toBeVisible();

  await page.getByRole('link', { name: 'My applications' }).click();
  const myRow = page.getByRole('row').filter({ hasText: animal.name });
  await expect(myRow.getByText('pending')).toBeVisible();
  await logout(page);

  await login(page, STAFF);
  await page.getByRole('link', { name: 'Staff panel' }).click();
  page.once('dialog', (dialog) => dialog.accept()); // "cannot be undone" confirmation
  const staffRow = page.getByRole('row').filter({ hasText: animal.name });
  await staffRow.getByRole('button', { name: 'Approve' }).click();
  await expect(staffRow.getByText('approved')).toBeVisible();
  await logout(page);

  await login(page, adopter);
  await expect(page.getByTestId('animal-card').filter({ hasText: animal.name }).getByText('Already adopted')).toBeVisible();
  await page.getByRole('link', { name: 'My applications' }).click();
  await expect(page.getByRole('row').filter({ hasText: animal.name }).getByText('approved')).toBeVisible();
});

test('visitors are asked to log in, adopters cannot open the staff panel', async ({ page }, testInfo) => {
  await page.goto('/');
  await expect(page.getByRole('link', { name: 'Log in to apply' }).first()).toBeVisible();

  const adopter = `${unique('nosy', testInfo)}@example.com`;
  await register(page, adopter);
  await login(page, adopter);
  await page.goto('/staff');
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByRole('link', { name: 'Staff panel' })).toHaveCount(0);
});
