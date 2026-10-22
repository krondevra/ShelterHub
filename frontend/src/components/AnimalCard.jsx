const STATUS_LABELS = {
  available: 'Available',
  pending: 'Pending',
  adopted: 'Adopted',
};

// `action`, if given, is rendered as a slot (e.g. an Apply button) so this
// component stays presentational and doesn't need to know about auth/applications.
export function AnimalCard({ animal, action }) {
  return (
    <article className="animal-card" data-testid="animal-card">
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
          <dd>{animal.age}</dd>
        </div>
      </dl>
      {action && <div className="animal-card-action">{action}</div>}
    </article>
  );
}
