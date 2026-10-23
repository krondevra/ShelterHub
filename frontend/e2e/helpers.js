import { expect } from '@playwright/test';

export const API_URL = process.env.E2E_API_URL ?? 'http://localhost:8000';
export const PASSWORD = 'password123';
export const STAFF = 'staff@example.com'; // from the demo seed

// Unique per run and per browser, so the tests can run again on the same database.
export function unique(prefix, testInfo) {
  return `${prefix}-${testInfo.project.name}-${Date.now()}`;
}

export async function login(page, email, password = PASSWORD) {
  await page.goto('/login');
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: 'Log in' }).click();
  await expect(page.getByRole('button', { name: 'Log out' })).toBeVisible();
}

export async function logout(page) {
  await page.getByRole('button', { name: 'Log out' }).click();
  await expect(page.getByRole('link', { name: 'Log in' })).toBeVisible();
}

export async function register(page, email, role = 'adopter') {
  await page.goto('/register');
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password').fill(PASSWORD);
  await page.getByLabel('I am a').selectOption(role);
  await page.getByRole('button', { name: 'Register' }).click();
  await expect(page.getByRole('heading', { name: 'Account created' })).toBeVisible();
}

// Creates an animal straight through the API (as the demo staff), so each
// test has its own animal in a known state.
export async function createAnimal(request, name) {
  const login = await request.post(`${API_URL}/auth/login`, { data: { email: STAFF, password: PASSWORD } });
  const { access_token } = await login.json();
  const response = await request.post(`${API_URL}/animals`, {
    headers: { Authorization: `Bearer ${access_token}` },
    data: { name, species: 'Dog', breed: 'Mixed', age: 2, shelter_id: 1 },
  });
  expect(response.status()).toBe(201);
  return response.json();
}

// A real 1x1 PNG, so the backend's format check accepts it.
export const PIXEL_PNG = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC',
  'base64'
);
