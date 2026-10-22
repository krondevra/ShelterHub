import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { AnimalCard } from './AnimalCard';

const animal = {
  id: 1,
  name: 'Rex',
  species: 'Dog',
  breed: 'Labrador',
  age: 3,
  status: 'available',
  shelter_id: 1,
};

describe('AnimalCard', () => {
  it('renders name, species, breed, age and status', () => {
    render(<AnimalCard animal={animal} />);
    expect(screen.getByRole('heading', { name: 'Rex' })).toBeInTheDocument();
    expect(screen.getByText('Dog')).toBeInTheDocument();
    expect(screen.getByText('Labrador')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('Available')).toBeInTheDocument();
  });

  it('falls back to the raw status if unrecognized', () => {
    render(<AnimalCard animal={{ ...animal, status: 'unknown' }} />);
    expect(screen.getByText('unknown')).toBeInTheDocument();
  });

  it('renders the action slot when provided', () => {
    render(<AnimalCard animal={animal} action={<button>Apply to adopt</button>} />);
    expect(screen.getByRole('button', { name: 'Apply to adopt' })).toBeInTheDocument();
  });

  it('renders no action when none is provided', () => {
    render(<AnimalCard animal={animal} />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});
