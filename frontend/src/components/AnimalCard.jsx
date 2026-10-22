import { useState } from 'react';
import { BASE_URL } from '../api/client';

const STATUS_LABELS = {
  available: 'Available',
  pending: 'Pending',
  adopted: 'Adopted',
};

// A soft-coloured icon placeholder for animals without a photo. Matches by
// substring rather than exact value, since `species` is free text (e.g. a
// shelter might record "Stray dog").
function speciesVisual(species) {
  const s = (species || '').toLowerCase();
  if (s.includes('dog')) return { emoji: '🐶', category: 'dog' };
  if (s.includes('cat')) return { emoji: '🐱', category: 'cat' };
  return { emoji: '🐾', category: 'other' };
}

export function formatAge(age) {
  if (age <= 0) return 'Under 1 year';
  if (age === 1) return '1 year';
  return `${age} years`;
}

// `action`, if given, is rendered as a slot (e.g. an Apply button) so this
// component stays presentational and doesn't need to know about auth/applications.
export function AnimalCard({ animal, action }) {
  const { emoji, category } = speciesVisual(animal.species);
  // Remember which URL failed, not just "failed": a new upload gets a new URL
  // and should be tried again without a page reload.
  const [failedUrl, setFailedUrl] = useState(null);
  const showPhoto = animal.photo_url && animal.photo_url !== failedUrl;

  return (
    <article className="animal-card" data-testid="animal-card">
      <div className={`animal-visual animal-visual-${category}`}>
        {showPhoto ? (
          <img
            src={`${BASE_URL}${animal.photo_url}`}
            alt={`Photo of ${animal.name}`}
            className="animal-visual-photo"
            onError={() => setFailedUrl(animal.photo_url)}
          />
        ) : (
          <span className="animal-visual-icon" aria-hidden="true">
            {emoji}
          </span>
        )}
      </div>
      <div className="animal-card-body">
        <div className="animal-card-header">
          <h3>{animal.name}</h3>
          <span className={`status-badge status-${animal.status}`}>
            {STATUS_LABELS[animal.status] ?? animal.status}
          </span>
        </div>
        <dl className="animal-card-details">
          <div>
            <dt>Species</dt>
            <dd>{animal.species}</dd>
          </div>
          <div>
            <dt>Breed</dt>
            <dd>{animal.breed}</dd>
          </div>
          <div>
            <dt>Age</dt>
            <dd>{formatAge(animal.age)}</dd>
          </div>
        </dl>
        {action && <div className="animal-card-action">{action}</div>}
      </div>
    </article>
  );
}
