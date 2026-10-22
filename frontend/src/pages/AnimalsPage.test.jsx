import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AnimalsPage } from './AnimalsPage';

const animals = [
  { id: 1, name: 'Rex', species: 'Dog', breed: 'Labrador', age: 3, status: 'available', shelter_id: 1 },
  { id: 2, name: 'Mia', species: 'Cat', breed: 'Tabby', age: 2, status: 'pending', shelter_id: 1 },
  { id: 3, name: 'Buddy', species: 'Dog', breed: 'Beagle', age: 5, status: 'adopted', shelter_id: 1 },
];

const createApplicationRun = vi.fn();
const refetchAnimals = vi.fn();
const refetchMyApplications = vi.fn();
let myApplications = [];
let authState = { isAuthenticated: false, user: null };

vi.mock('../hooks/useAnimals', () => ({
  useAnimals: () => ({ data: animals, loading: false, error: null, refetch: refetchAnimals }),
  useShelters: () => ({ data: [{ id: 1, name: 'Paws Haven', city: 'Riga' }], loading: false, error: null }),
}));

vi.mock('../hooks/useApplications', () => ({
  useApplications: ({ skip } = {}) => ({
    data: skip ? null : myApplications,
    loading: false,
    error: null,
    refetch: refetchMyApplications,
  }),
  useCreateApplication: () => ({ run: createApplicationRun, loading: false, error: null }),
}));

vi.mock('../hooks/useAuth', () => ({
  useAuth: () => authState,
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <AnimalsPage />
    </MemoryRouter>
  );
}

describe('AnimalsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    createApplicationRun.mockResolvedValue({});
    myApplications = [];
    authState = { isAuthenticated: false, user: null };
  });

  it('prompts anonymous visitors to log in instead of showing an apply button', () => {
    renderPage();
    expect(screen.getAllByText('Log in to apply')).toHaveLength(3);
    expect(screen.queryByRole('button', { name: 'Apply to adopt' })).not.toBeInTheDocument();
  });

  it('shows Apply to adopt for an adopter with no existing application, and Already adopted for an adopted animal', () => {
    authState = { isAuthenticated: true, user: { id: '1', role: 'adopter' } };
    renderPage();
    expect(screen.getAllByRole('button', { name: 'Apply to adopt' })).toHaveLength(2);
    expect(screen.getByText('Already adopted')).toBeInTheDocument();
  });

  it('shows "Application submitted" for an animal with a pending application, even before clicking Apply', () => {
    authState = { isAuthenticated: true, user: { id: '1', role: 'adopter' } };
    myApplications = [{ id: 10, animal_id: 1, adopter_id: 1, status: 'pending', created_at: '2026-01-01' }];
    renderPage();

    expect(screen.getByText('Application submitted')).toBeInTheDocument();
    // Mia (id 2) has no application yet, so it still offers Apply.
    expect(screen.getByRole('button', { name: 'Apply to adopt' })).toBeInTheDocument();
  });

  it('does not treat a rejected application as still pending', () => {
    authState = { isAuthenticated: true, user: { id: '1', role: 'adopter' } };
    myApplications = [{ id: 10, animal_id: 1, adopter_id: 1, status: 'rejected', created_at: '2026-01-01' }];
    renderPage();

    expect(screen.getAllByRole('button', { name: 'Apply to adopt' })).toHaveLength(2);
  });

  it('refetches animals and my-applications after a successful apply', async () => {
    authState = { isAuthenticated: true, user: { id: '1', role: 'adopter' } };
    renderPage();

    fireEvent.click(screen.getAllByRole('button', { name: 'Apply to adopt' })[0]);

    await vi.waitFor(() => expect(createApplicationRun).toHaveBeenCalledWith(1));
    await vi.waitFor(() => expect(refetchAnimals).toHaveBeenCalled());
    expect(refetchMyApplications).toHaveBeenCalled();
  });

  it('shows an inline error if applying fails (e.g. a 409 for an already-pending application)', async () => {
    authState = { isAuthenticated: true, user: { id: '1', role: 'adopter' } };
    createApplicationRun.mockRejectedValueOnce(new Error('You already have a pending application for this animal'));
    renderPage();

    fireEvent.click(screen.getAllByRole('button', { name: 'Apply to adopt' })[0]);

    expect(await screen.findByText('You already have a pending application for this animal')).toBeInTheDocument();
  });
});
