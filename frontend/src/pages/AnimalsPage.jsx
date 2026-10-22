import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { AnimalCard } from '../components/AnimalCard';
import { ShelterOverview } from '../components/ShelterOverview';
import { Spinner } from '../components/Spinner';
import { useAnimals, useShelters } from '../hooks/useAnimals';
import { useApplications, useCreateApplication } from '../hooks/useApplications';
import { useAuth } from '../hooks/useAuth';

export function AnimalsPage() {
  const { data: animals, loading, error, refetch } = useAnimals();
  const { data: shelters, loading: sheltersLoading, error: sheltersError } = useShelters();
  const { isAuthenticated, user } = useAuth();
  const isAdopter = isAuthenticated && user.role === 'adopter';
  const { data: myApplications, refetch: refetchMyApplications } = useApplications({ skip: !isAdopter });
  const createApplication = useCreateApplication();
  const [cardState, setCardState] = useState({}); // { [animalId]: { error?: string } }

  // Survives a reload: an animal with a pending application from this adopter
  // shows "Application submitted" even before `cardState` has anything in it.
  const pendingAnimalIds = useMemo(() => {
    const ids = new Set();
    for (const application of myApplications ?? []) {
      if (application.status === 'pending') ids.add(application.animal_id);
    }
    return ids;
  }, [myApplications]);

  async function apply(animalId) {
    setCardState((s) => ({ ...s, [animalId]: {} }));
    try {
      await createApplication.run(animalId);
      refetch(); // animal status may have flipped to "pending"
      refetchMyApplications();
    } catch (e) {
      setCardState((s) => ({ ...s, [animalId]: { error: e.message } }));
    }
  }

  return (
    <>
      <section className="hero">
        <h1>Every animal deserves a loving home</h1>
        <p>
          ShelterHub brings together rescue shelters across the Baltics in one place, so every dog and cat
          waiting for a home is easier to find — and easier to adopt. Browse the animals below, submit an
          adoption application in minutes, and our shelter staff will take it from there.
        </p>
      </section>

      {!loading && !error && !sheltersLoading && !sheltersError && (
        <ShelterOverview shelters={shelters} animals={animals} />
      )}

      <section>
        <h2>Animals looking for a home</h2>
        {loading && <Spinner label="Loading animals…" />}
        {error && <p className="form-error">Could not load animals: {error}</p>}
        {!loading && !error && animals.length === 0 && (
          <p className="empty-state">No animals yet. Check back soon!</p>
        )}
        {!loading && !error && (
          <div className="animal-grid">
            {animals.map((animal) => {
              const state = cardState[animal.id] ?? {};
              let action = null;

              if (isAdopter) {
                if (animal.status === 'adopted') {
                  action = <span className="muted">Already adopted</span>;
                } else if (pendingAnimalIds.has(animal.id)) {
                  action = <span className="muted">Application submitted</span>;
                } else {
                  action = (
                    <>
                      <button type="button" onClick={() => apply(animal.id)} disabled={createApplication.loading}>
                        {createApplication.loading ? 'Applying…' : 'Apply to adopt'}
                      </button>
                      {state.error && <p className="form-error">{state.error}</p>}
                    </>
                  );
                }
              } else if (!isAuthenticated) {
                action = <Link to="/login">Log in to apply</Link>;
              }

              return <AnimalCard key={animal.id} animal={animal} action={action} />;
            })}
          </div>
        )}
      </section>
    </>
  );
}
