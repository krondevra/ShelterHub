// Mirrors the agreed POST /animals/{id}/photo contract: JPEG, PNG or WebP,
// at most 5 MB. Checked client-side before uploading so a bad file never
// makes the round trip; the backend's 415/413 errors are the fallback if it
// still fails.
export const MAX_PHOTO_BYTES = 5 * 1024 * 1024;
export const ALLOWED_PHOTO_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

export function validatePhotoFile(file) {
  if (!ALLOWED_PHOTO_TYPES.includes(file.type)) {
    return { valid: false, error: 'Photo must be a JPEG, PNG, or WebP image.' };
  }
  if (file.size > MAX_PHOTO_BYTES) {
    return { valid: false, error: 'Photo must be 5 MB or smaller.' };
  }
  return { valid: true };
}
