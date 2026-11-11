import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { AnimalCard, formatAge } from './AnimalCard';

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
    expect(screen.getByText('3 years')).toBeInTheDocument();
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

  it.each([
    ['dog', '🐶'],
    ['Labrador dog', '🐶'],
    ['cat', '🐱'],
    ['Siamese cat', '🐱'],
    ['rabbit', '🐾'],
    ['', '🐾'],
  ])('shows the %s species icon', (species, emoji) => {
    render(<AnimalCard animal={{ ...animal, species }} />);
    expect(screen.getByText(emoji)).toBeInTheDocument();
  });

  it('shows the species icon (not a photo) when photo_url is null', () => {
    render(<AnimalCard animal={{ ...animal, photo_url: null }} />);
    expect(screen.getByText('🐶')).toBeInTheDocument();
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
  });

  it('shows the photo instead of the icon when photo_url is set', () => {
    render(<AnimalCard animal={{ ...animal, photo_url: '/uploads/animals/1.jpg' }} />);
    const img = screen.getByRole('img', { name: 'Photo of Rex' });
    expect(img).toBeInTheDocument();
    expect(img.src).toBe('http://localhost:8000/uploads/animals/1.jpg');
    expect(screen.queryByText('🐶')).not.toBeInTheDocument();
  });

  it('falls back to the species icon if the photo fails to load', () => {
    render(<AnimalCard animal={{ ...animal, photo_url: '/uploads/animals/1.jpg' }} />);
    const img = screen.getByRole('img', { name: 'Photo of Rex' });

    fireEvent.error(img);

    expect(screen.queryByRole('img')).not.toBeInTheDocument();
    expect(screen.getByText('🐶')).toBeInTheDocument();
  });

  it('opens the full photo and closes it with the close button', () => {
    render(<AnimalCard animal={{ ...animal, photo_url: '/uploads/animals/1.jpg' }} />);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'View full photo of Rex' }));

    const dialog = screen.getByRole('dialog', { name: 'Photo of Rex' });
    expect(dialog.querySelector('img').src).toBe('http://localhost:8000/uploads/animals/1.jpg');

    fireEvent.click(screen.getByRole('button', { name: 'Close photo' }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('closes the full photo with Escape and a click on the background', () => {
    render(<AnimalCard animal={{ ...animal, photo_url: '/uploads/animals/1.jpg' }} />);
    const open = screen.getByRole('button', { name: 'View full photo of Rex' });

    fireEvent.click(open);
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

    fireEvent.click(open);
    fireEvent.click(screen.getByRole('dialog'));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('keeps the full photo open when the photo itself is clicked', () => {
    render(<AnimalCard animal={{ ...animal, photo_url: '/uploads/animals/1.jpg' }} />);
    fireEvent.click(screen.getByRole('button', { name: 'View full photo of Rex' }));

    fireEvent.click(screen.getByRole('dialog').querySelector('img'));
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('has no view button when there is no photo', () => {
    render(<AnimalCard animal={{ ...animal, photo_url: null }} />);
    expect(screen.queryByRole('button', { name: /View full photo/ })).not.toBeInTheDocument();
  });

  it('tries again when a failed photo is replaced by a new one', () => {
    const { rerender } = render(<AnimalCard animal={{ ...animal, photo_url: '/uploads/animals/1-old.jpg' }} />);
    fireEvent.error(screen.getByRole('img', { name: 'Photo of Rex' }));

    rerender(<AnimalCard animal={{ ...animal, photo_url: '/uploads/animals/1-new.jpg' }} />);

    const img = screen.getByRole('img', { name: 'Photo of Rex' });
    expect(img.src).toBe('http://localhost:8000/uploads/animals/1-new.jpg');
  });
});

describe('formatAge', () => {
  it('shows "Under 1 year" for age 0', () => {
    expect(formatAge(0)).toBe('Under 1 year');
  });

  it('uses the singular for age 1', () => {
    expect(formatAge(1)).toBe('1 year');
  });

  it('uses the plural for ages above 1', () => {
    expect(formatAge(2)).toBe('2 years');
    expect(formatAge(15)).toBe('15 years');
  });
});
