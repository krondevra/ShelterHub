import { describe, expect, it } from 'vitest';
import { loginSchema, registerSchema } from './authSchemas';
import { validate } from './validate';

describe('registerSchema', () => {
  it('accepts a valid registration', () => {
    const { values, errors } = validate(registerSchema, {
      email: 'adopter@example.com',
      password: 'password123',
      role: 'adopter',
    });
    expect(errors).toEqual({});
    expect(values).toEqual({
      email: 'adopter@example.com',
      password: 'password123',
      role: 'adopter',
    });
  });

  it('rejects a password shorter than 8 characters', () => {
    const { values, errors } = validate(registerSchema, {
      email: 'a@example.com',
      password: 'short1',
      role: 'adopter',
    });
    expect(values).toBeNull();
    expect(errors.password).toMatch(/at least 8/);
  });

  it('rejects a password over 72 characters', () => {
    const { values, errors } = validate(registerSchema, {
      email: 'a@example.com',
      password: 'a'.repeat(73),
      role: 'adopter',
    });
    expect(values).toBeNull();
    expect(errors.password).toMatch(/at most 72 characters/);
  });

  it('rejects a password within 72 chars but over 72 UTF-8 bytes', () => {
    // 'é' as a precomposed single char is 1 char but 2 bytes in UTF-8.
    const password = 'é'.repeat(72); // 72 chars, 144 bytes
    const { values, errors } = validate(registerSchema, {
      email: 'a@example.com',
      password,
      role: 'adopter',
    });
    expect(values).toBeNull();
    expect(errors.password).toMatch(/72 bytes/);
  });

  it('accepts a password that is exactly 72 bytes of multi-byte characters', () => {
    const password = 'é'.repeat(36); // 36 chars, 72 bytes
    const { values, errors } = validate(registerSchema, {
      email: 'a@example.com',
      password,
      role: 'adopter',
    });
    expect(errors).toEqual({});
    expect(values.password).toBe(password);
  });

  it('rejects an invalid email', () => {
    const { values, errors } = validate(registerSchema, {
      email: 'not-an-email',
      password: 'password123',
      role: 'adopter',
    });
    expect(values).toBeNull();
    expect(errors.email).toBeDefined();
  });

  it('rejects a role outside adopter/staff', () => {
    const { values, errors } = validate(registerSchema, {
      email: 'a@example.com',
      password: 'password123',
      role: 'admin',
    });
    expect(values).toBeNull();
    expect(errors.role).toBeDefined();
  });
});

describe('loginSchema', () => {
  it('requires both email and password', () => {
    const { values, errors } = validate(loginSchema, { email: '', password: '' });
    expect(values).toBeNull();
    expect(errors.email).toBeDefined();
    expect(errors.password).toBeDefined();
  });

  it('accepts valid credentials regardless of password length rules', () => {
    // Login only checks presence, not the registration password policy.
    const { values, errors } = validate(loginSchema, { email: 'a@example.com', password: 'x' });
    expect(errors).toEqual({});
    expect(values).toEqual({ email: 'a@example.com', password: 'x' });
  });
});
