import { useState } from 'react';
import { buildAnimalPatch } from '../hooks/useAnimals';
import { animalSchema } from '../validation/animalSchemas';
import { validate } from '../validation/validate';

// Status is intentionally not a field here: it only ever changes through the
// application flow (apply -> pending, approve -> adopted), never via this form.
export function AnimalForm({ mode, animal, shelters, onSubmit, onCancel }) {
  const [form, setForm] = useState({
    name: animal?.name ?? '',
    species: animal?.species ?? '',
    breed: animal?.breed ?? '',
    age: animal?.age ?? '',
    shelter_id: animal?.shelter_id ?? '',
  });
  const [fieldErrors, setFieldErrors] = useState({});
  const [submitError, setSubmitError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  function update(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const { values, errors } = validate(animalSchema, form);
    setFieldErrors(errors);
    if (!values) return;

    const payload = mode === 'edit' ? buildAnimalPatch(animal, values) : values;
    if (mode === 'edit' && Object.keys(payload).length === 0) {
      setSubmitError('No changes to save.');
      return;
    }

    setSubmitting(true);
    setSubmitError(null);
    try {
      await onSubmit(payload);
    } catch (err) {
      setSubmitError(err.message);
      setSubmitting(false);
    }
  }

  return (
    <form className="animal-form" onSubmit={handleSubmit} noValidate>
      <label>
        Name
        <input value={form.name} onChange={update('name')} />
      </label>
      {fieldErrors.name && <p className="form-error">{fieldErrors.name}</p>}

      <label>
        Species
        <input value={form.species} onChange={update('species')} />
      </label>
      {fieldErrors.species && <p className="form-error">{fieldErrors.species}</p>}

      <label>
        Breed
        <input value={form.breed} onChange={update('breed')} />
      </label>
      {fieldErrors.breed && <p className="form-error">{fieldErrors.breed}</p>}

      <label>
        Age
        <input type="number" min="0" value={form.age} onChange={update('age')} />
      </label>
      {fieldErrors.age && <p className="form-error">{fieldErrors.age}</p>}

      <label>
        Shelter
        <select value={form.shelter_id} onChange={update('shelter_id')}>
          <option value="">Select a shelter</option>
          {shelters.map((shelter) => (
            <option key={shelter.id} value={shelter.id}>
              {shelter.name}
              {shelter.city ? ` — ${shelter.city}` : ''}
            </option>
          ))}
        </select>
      </label>
      {fieldErrors.shelter_id && <p className="form-error">{fieldErrors.shelter_id}</p>}

      {submitError && <p className="form-error">{submitError}</p>}

      <div className="animal-form-actions">
        <button type="submit" disabled={submitting}>
          {submitting ? 'Saving…' : mode === 'edit' ? 'Save changes' : 'Add animal'}
        </button>
        {onCancel && (
          <button type="button" className="btn-secondary" onClick={onCancel} disabled={submitting}>
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}
