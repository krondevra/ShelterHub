import { useId, useRef, useState } from 'react';
import { BASE_URL } from '../api/client';
import { useDeleteAnimalPhoto, useUploadAnimalPhoto } from '../hooks/useAnimals';
import { validatePhotoFile } from '../validation/photoValidation';

// A per-animal photo picker: preview, then Upload/Remove. Works the same
// right after creating a new animal (the row just appears with photo_url:
// null, same as any other animal) as it does for an existing one.
export function PhotoControl({ animalId, photoUrl, onChange }) {
  const inputId = useId();
  const fileInputRef = useRef(null);
  const [pendingFile, setPendingFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [validationError, setValidationError] = useState(null);
  const upload = useUploadAnimalPhoto();
  const remove = useDeleteAnimalPhoto();

  function resetPicker() {
    setPendingFile(null);
    setPreviewUrl(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  }

  function handleFileChange(e) {
    const selected = e.target.files?.[0] ?? null;
    setValidationError(null);
    if (!selected) {
      resetPicker();
      return;
    }
    const result = validatePhotoFile(selected);
    if (!result.valid) {
      setValidationError(result.error);
      resetPicker();
      return;
    }
    setPendingFile(selected);
    setPreviewUrl(URL.createObjectURL(selected));
  }

  async function handleUpload() {
    if (!pendingFile) return;
    try {
      const updated = await upload.run(animalId, pendingFile);
      resetPicker();
      onChange?.(updated);
    } catch {
      // upload.error is rendered below
    }
  }

  async function handleRemove() {
    try {
      const updated = await remove.run(animalId);
      onChange?.(updated);
    } catch {
      // remove.error is rendered below
    }
  }

  const displayUrl = previewUrl ?? (photoUrl ? `${BASE_URL}${photoUrl}` : null);
  const error = validationError || upload.error || remove.error;

  return (
    <div className="photo-control">
      {displayUrl ? (
        <img src={displayUrl} alt="Animal preview" className="photo-control-preview" />
      ) : (
        <span className="muted">No photo</span>
      )}
      <div className="photo-control-actions">
        <label htmlFor={inputId} className="btn-secondary photo-control-pick">
          Choose photo
        </label>
        <input
          id={inputId}
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={handleFileChange}
          className="photo-control-input"
        />
        {pendingFile && (
          <button type="button" onClick={handleUpload} disabled={upload.loading}>
            {upload.loading ? 'Uploading…' : 'Upload'}
          </button>
        )}
        {photoUrl && !pendingFile && (
          <button type="button" className="btn-danger-outline" onClick={handleRemove} disabled={remove.loading}>
            {remove.loading ? 'Removing…' : 'Remove'}
          </button>
        )}
      </div>
      {error && <p className="form-error">{error}</p>}
    </div>
  );
}
