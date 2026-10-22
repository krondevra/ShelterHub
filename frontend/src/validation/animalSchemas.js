import { z } from 'zod';

// Mirrors the backend's Animal fields that are actually writable:
// name/species/breed non-empty (with the backend's max lengths: name 120,
// species 80, breed 120 -- see AnimalCreate in backend/app/schemas.py), age a
// 32-bit non-negative integer, shelter_id picked from the GET /shelters list
// (never free text).
export const animalSchema = z.object({
  name: z.string().trim().min(1, 'Name is required').max(120, 'Name must be at most 120 characters'),
  species: z.string().trim().min(1, 'Species is required').max(80, 'Species must be at most 80 characters'),
  breed: z.string().trim().min(1, 'Breed is required').max(120, 'Breed must be at most 120 characters'),
  age: z.coerce
    .number({ message: 'Age is required' })
    .int('Age must be a whole number')
    .min(0, 'Age cannot be negative')
    .max(2147483647, 'Age is too large'),
  shelter_id: z.coerce.number({ message: 'Select a shelter' }).int().min(1, 'Select a shelter'),
});
