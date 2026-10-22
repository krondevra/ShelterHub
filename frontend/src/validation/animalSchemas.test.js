import { describe, expect, it } from 'vitest';
import { animalSchema } from './animalSchemas';
import { validate } from './validate';

const base = { name: 'Rex', species: 'Dog', breed: 'Labrador', age: '3', shelter_id: '1' };

describe('animalSchema', () => {
  it('accepts valid form input and coerces age/shelter_id to numbers', () => {
    const { values, errors } = validate(animalSchema, base);
    expect(errors).toEqual({});
    expect(values).toEqual({ name: 'Rex', species: 'Dog', breed: 'Labrador', age: 3, shelter_id: 1 });
  });

  it.each(['name', 'species', 'breed'])('rejects an empty %s', (field) => {
    const { values, errors } = validate(animalSchema, { ...base, [field]: '' });
    expect(values).toBeNull();
    expect(errors[field]).toBeDefined();
  });

  it('rejects a negative age', () => {
    const { values, errors } = validate(animalSchema, { ...base, age: '-1' });
    expect(values).toBeNull();
    expect(errors.age).toBeDefined();
  });

  it('rejects a non-integer age', () => {
    const { values, errors } = validate(animalSchema, { ...base, age: '2.5' });
    expect(values).toBeNull();
    expect(errors.age).toBeDefined();
  });

  it('rejects an age beyond the 32-bit integer range', () => {
    const { values, errors } = validate(animalSchema, { ...base, age: '2147483648' });
    expect(values).toBeNull();
    expect(errors.age).toBeDefined();
  });

  it('requires a shelter to be selected', () => {
    const { values, errors } = validate(animalSchema, { ...base, shelter_id: '' });
    expect(values).toBeNull();
    expect(errors.shelter_id).toBeDefined();
  });
});
