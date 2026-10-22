import { describe, expect, it } from 'vitest';
import { shelterCounts } from './ShelterOverview';

const animals = [
  { id: 1, shelter_id: 1, status: 'available' },
  { id: 2, shelter_id: 1, status: 'pending' },
  { id: 3, shelter_id: 1, status: 'adopted' },
  { id: 4, shelter_id: 2, status: 'available' },
];

describe('shelterCounts', () => {
  it('counts animals by status for the given shelter', () => {
    expect(shelterCounts(animals, 1)).toEqual({ total: 3, available: 1, pending: 1, adopted: 1 });
  });

  it('only counts animals belonging to that shelter', () => {
    expect(shelterCounts(animals, 2)).toEqual({ total: 1, available: 1, pending: 0, adopted: 0 });
  });

  it('returns all zeros for a shelter with no animals', () => {
    expect(shelterCounts(animals, 99)).toEqual({ total: 0, available: 0, pending: 0, adopted: 0 });
  });
});
