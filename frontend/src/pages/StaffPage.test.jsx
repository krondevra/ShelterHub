import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ApplicationsTab } from './StaffPage';

const refetchApplications = vi.fn();
const refetchAnimals = vi.fn();
const updateStatusRun = vi.fn();

vi.mock('../hooks/useApplications', () => ({
  useApplications: () => ({
    data: [
      { id: 1, adopter_id: 10, animal_id: 1, status: 'pending', created_at: '2026-01-01T00:00:00Z' },
      { id: 2, adopter_id: 11, animal_id: 2, status: 'approved', created_at: '2026-01-02T00:00:00Z' },
    ],
    loading: false,
    error: null,
    refetch: refetchApplications,
  }),
  useUpdateApplicationStatus: () => ({ run: updateStatusRun, loading: false, error: null }),
}));

vi.mock('../hooks/useAnimals', () => ({
  useAnimals: () => ({
    data: [
      { id: 1, name: 'Rex', species: 'Dog', breed: 'Lab', age: 3, status: 'pending', shelter_id: 1 },
      { id: 2, name: 'Mia', species: 'Cat', breed: 'Tabby', age: 2, status: 'adopted', shelter_id: 1 },
    ],
    loading: false,
    error: null,
    refetch: refetchAnimals,
  }),
}));

describe('ApplicationsTab status transitions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    updateStatusRun.mockResolvedValue({});
  });

  it('only offers Approve/Reject for pending applications', () => {
    render(<ApplicationsTab />);
    expect(screen.getAllByRole('button', { name: 'Approve' })).toHaveLength(1);
    expect(screen.getAllByRole('button', { name: 'Reject' })).toHaveLength(1);
    expect(screen.getByText('Decided')).toBeInTheDocument();
  });

  it('asks for confirmation before approving, and does nothing if cancelled', () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false);
    render(<ApplicationsTab />);

    fireEvent.click(screen.getByRole('button', { name: 'Approve' }));

    expect(window.confirm).toHaveBeenCalled();
    expect(updateStatusRun).not.toHaveBeenCalled();
  });

  it('approves after confirmation and refetches both applications and animals', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    render(<ApplicationsTab />);

    fireEvent.click(screen.getByRole('button', { name: 'Approve' }));

    await waitFor(() => expect(updateStatusRun).toHaveBeenCalledWith(1, 'approved'));
    await waitFor(() => expect(refetchApplications).toHaveBeenCalled());
    expect(refetchAnimals).toHaveBeenCalled();
  });

  it('rejects without asking for confirmation', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false);
    render(<ApplicationsTab />);

    fireEvent.click(screen.getByRole('button', { name: 'Reject' }));

    expect(window.confirm).not.toHaveBeenCalled();
    await waitFor(() => expect(updateStatusRun).toHaveBeenCalledWith(1, 'rejected'));
  });

  it('surfaces a 409 error (e.g. already decided) inline without crashing', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    updateStatusRun.mockRejectedValueOnce(new Error('Application has already been decided'));
    render(<ApplicationsTab />);

    fireEvent.click(screen.getByRole('button', { name: 'Approve' }));

    expect(await screen.findByText('Application has already been decided')).toBeInTheDocument();
  });
});
