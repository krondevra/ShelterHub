import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { PhotoControl } from './PhotoControl';

vi.mock('../hooks/useAnimals', () => ({
  useUploadAnimalPhoto: () => ({ run: vi.fn(), loading: false, error: null }),
  useDeleteAnimalPhoto: () => ({ run: vi.fn(), loading: false, error: null }),
}));

function pick(file) {
  fireEvent.change(screen.getByLabelText('Choose photo'), { target: { files: [file] } });
}

const png = (name) => new File(['x'], name, { type: 'image/png' });

describe('PhotoControl preview URLs', () => {
  let counter;

  beforeEach(() => {
    counter = 0;
    // jsdom has no blob: URLs, so stand in for them.
    URL.createObjectURL = vi.fn(() => `blob:preview-${++counter}`);
    URL.revokeObjectURL = vi.fn();
  });

  afterEach(() => {
    cleanup(); // unmount first: unmounting still calls revokeObjectURL
    delete URL.createObjectURL;
    delete URL.revokeObjectURL;
  });

  it('revokes the old preview when another file is picked', () => {
    render(<PhotoControl animalId={1} photoUrl={null} />);

    pick(png('a.png'));
    expect(screen.getByAltText('Animal preview')).toHaveAttribute('src', 'blob:preview-1');

    pick(png('b.png'));
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:preview-1');
    expect(screen.getByAltText('Animal preview')).toHaveAttribute('src', 'blob:preview-2');
  });

  it('revokes the preview on unmount', () => {
    const { unmount } = render(<PhotoControl animalId={1} photoUrl={null} />);
    pick(png('a.png'));

    unmount();

    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:preview-1');
  });
});
