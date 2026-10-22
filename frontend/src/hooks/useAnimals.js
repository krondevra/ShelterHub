import { useCallback } from 'react';
import { api } from '../api/client';
import { useMutation, useQuery } from './useQuery';

const PATCHABLE_FIELDS = ['name', 'species', 'breed', 'age', 'shelter_id'];

// The backend's PATCH /animals/{id} is strict: only the fields that actually
// changed, from PATCHABLE_FIELDS, and never null (sending status/id/unknown
// keys or a null value is a 422). Build the diff from the loaded animal and
// the edited form values.
export function buildAnimalPatch(original, edited) {
  const patch = {};
  for (const field of PATCHABLE_FIELDS) {
    const value = edited[field];
    if (value === undefined || value === null) continue;
    if (value !== original[field]) patch[field] = value;
  }
  return patch;
}

export function useAnimals() {
  const fetcher = useCallback(() => api.get('/animals'), []);
  return useQuery(fetcher);
}

export function useAnimal(id) {
  const fetcher = useCallback(() => api.get(`/animals/${id}`), [id]);
  return useQuery(fetcher, { skip: id == null });
}

export function useShelters() {
  const fetcher = useCallback(() => api.get('/shelters'), []);
  return useQuery(fetcher);
}

export function useCreateAnimal() {
  return useMutation((animal) => api.post('/animals', animal));
}

export function useUpdateAnimal() {
  return useMutation((id, patch) => api.patch(`/animals/${id}`, patch));
}

// photo_url is never part of POST/PATCH /animals (422 if sent there, same as
// status) -- it's managed only through these two endpoints.
export function useUploadAnimalPhoto() {
  return useMutation((id, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.upload(`/animals/${id}/photo`, formData);
  });
}

export function useDeleteAnimalPhoto() {
  return useMutation((id) => api.delete(`/animals/${id}/photo`));
}
