import { useCallback } from 'react';
import { api } from '../api/client';
import { useMutation, useQuery } from './useQuery';

// GET /applications is role-aware server-side: staff get all, adopters get
// only their own. Same hook works for both panels.
export function useApplications() {
  const fetcher = useCallback(() => api.get('/applications'), []);
  return useQuery(fetcher);
}

export function useCreateApplication() {
  return useMutation((animalId) => api.post('/applications', { animal_id: animalId }));
}

export function useUpdateApplicationStatus() {
  return useMutation((id, status) => api.patch(`/applications/${id}`, { status }));
}
