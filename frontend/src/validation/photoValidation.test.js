import { describe, expect, it } from 'vitest';
import { MAX_PHOTO_BYTES, validatePhotoFile } from './photoValidation';

function makeFile({ type = 'image/jpeg', size = 1024 } = {}) {
  // jsdom's File doesn't compute `size` from content reliably across
  // versions, so a Blob-backed File is used and `size` is asserted directly.
  const file = new File([new Uint8Array(size)], 'photo', { type });
  return file;
}

describe('validatePhotoFile', () => {
  it.each(['image/jpeg', 'image/png', 'image/webp'])('accepts a %s file under the size limit', (type) => {
    const result = validatePhotoFile(makeFile({ type, size: 1024 }));
    expect(result).toEqual({ valid: true });
  });

  it('accepts a file at exactly the 5 MB limit', () => {
    const result = validatePhotoFile(makeFile({ size: MAX_PHOTO_BYTES }));
    expect(result).toEqual({ valid: true });
  });

  it('rejects a file one byte over the 5 MB limit', () => {
    const result = validatePhotoFile(makeFile({ size: MAX_PHOTO_BYTES + 1 }));
    expect(result.valid).toBe(false);
    expect(result.error).toMatch(/5 MB/);
  });

  it.each(['image/gif', 'application/pdf', 'text/plain', ''])('rejects a %s file', (type) => {
    const result = validatePhotoFile(makeFile({ type, size: 1024 }));
    expect(result.valid).toBe(false);
    expect(result.error).toMatch(/JPEG, PNG, or WebP/);
  });
});
