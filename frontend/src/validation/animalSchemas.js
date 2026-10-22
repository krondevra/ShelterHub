import { z } from 'zod';

// Mirrors the backend's Animal fields that are actually writable:
// name/species/breed non-empty, age a 32-bit non-negative integer,
// shelter_id picked from the GET /shelters list (never free text).
export const animalSchema = z.object({
  name: z.string().trim().min(1, 'Name is required'),
  species: z.string().trim().min(1, 'Species is required'),
  breed: z.string().trim().min(1, 'Breed is required'),
  age: z.coerce
    .number({ message: 'Age is required' })
    .int('Age must be a whole number')
    .min(0, 'Age cannot be negative')
    .max(2147483647, 'Age is too large'),
  shelter_id: z.coerce.number({ message: 'Select a shelter' }).int().min(1, 'Select a shelter'),
});
