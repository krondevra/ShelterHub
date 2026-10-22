import { SHELTER_INFO } from '../data/shelterInfo';

// Counts of animals at a given shelter, broken down by status.
// Pure so it can be unit-tested without rendering anything.
export function shelterCounts(animals, shelterId) {
  const atShelter = animals.filter((a) => a.shelter_id === shelterId);
  return {
    total: atShelter.length,
    available: atShelter.filter((a) => a.status === 'available').length,
    pending: atShelter.filter((a) => a.status === 'pending').length,
    adopted: atShelter.filter((a) => a.status === 'adopted').length,
  };
}

export function ShelterOverview({ shelters, animals }) {
  return (
    <section className="shelter-overview">
      <h2>Our shelters</h2>
      <div className="shelter-grid">
        {shelters.map((shelter) => {
          const counts = shelterCounts(animals, shelter.id);
          const info = SHELTER_INFO[shelter.name];
          const location = [shelter.city, info?.country].filter(Boolean).join(', ');
          return (
            <article key={shelter.id} className="shelter-card">
              <h3>{shelter.name}</h3>
              {location && <p className="muted">{location}</p>}
              {info?.description && <p className="shelter-description">{info.description}</p>}
              <p className="shelter-stats">
                {counts.total === 0
                  ? 'No animals yet'
                  : `${counts.total} animal${counts.total === 1 ? '' : 's'} · ${counts.available} available`}
              </p>
            </article>
          );
        })}
      </div>
    </section>
  );
}
