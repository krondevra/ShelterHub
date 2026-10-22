import { z } from 'zod';

// Mirrors the backend's Pydantic rule: 8-72 chars AND at most 72 UTF-8 bytes
// (accented/non-Latin characters can take more than one byte each).
const password = z
  .string()
  .min(8, 'Password must be at least 8 characters')
  .max(72, 'Password must be at most 72 characters')
  .refine((pw) => new TextEncoder().encode(pw).length <= 72, {
    message: 'Password must be at most 72 bytes (some characters use more than one byte)',
  });

export const registerSchema = z.object({
  email: z.string().trim().min(1, 'Email is required').email('Enter a valid email'),
  password,
  role: z.enum(['adopter', 'staff'], { message: 'Select a role' }),
});

export const loginSchema = z.object({
  email: z.string().trim().min(1, 'Email is required').email('Enter a valid email'),
  password: z.string().min(1, 'Password is required'),
});
