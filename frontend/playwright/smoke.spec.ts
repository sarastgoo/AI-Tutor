import { test, expect } from '@playwright/test';

test('Health page loads with correct title', async ({ page }) => {
  await page.goto('/');

  // Check page title
  await expect(page).toHaveTitle(/AI English Tutor/);

  // Check main heading
  await expect(page.getByRole('heading', { name: 'AI English Tutor' })).toBeVisible();

  // Check that the main layout elements are present (Backend card)
  await expect(page.getByText('Backend', { exact: true })).toBeVisible();
  
  // Check that the Database card is present
  await expect(page.getByText('Database', { exact: true })).toBeVisible();
});