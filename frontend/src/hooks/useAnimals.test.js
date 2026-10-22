import { describe, expect, it } from 'vitest';
import { buildAnimalPatch } from './useAnimals';

const original = { id: 7, name: 'Rex', species: 'Dog', breed: 'Labrador', age: 3, shelter_id: 1, status: 'available' };

describe('buildAnimalPatch', () => {
  it('includes only fields that changed', () => {
    const patch = buildAnimalPatch(original, { ...original, age: 4 });
    expect(patch).toEqual({ age: 4 });
  });

  it('returns an empty object when nothing changed', () => {
    const patch = buildAnimalPatch(original, { ...original });
    expect(patch).toEqual({});
  });

  it('never includes status, id, or unknown fields even if present on the edited object', () => {
    const patch = buildAnimalPatch(original, { ...original, status: 'adopted', id: 99, foo: 'bar', age: 5 });
    expect(patch).toEqual({ age: 5 });
  });

  it('never sends a null value for a changed field', () => {
    const patch = buildAnimalPatch(original, { ...original, breed: null, age: 5 });
    expect(patch).toEqual({ age: 5 });
  });

  it('can include multiple changed fields at once', () => {
    const patch = buildAnimalPatch(original, { ...original, name: 'Max', shelter_id: 2 });
    expect(patch).toEqual({ name: 'Max', shelter_id: 2 });
  });
});
