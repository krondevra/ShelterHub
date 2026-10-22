import { useMemo, useState } from 'react';
import { AnimalForm } from '../components/AnimalForm';
import { Spinner } from '../components/Spinner';
import { useAnimals, useCreateAnimal, useShelters, useUpdateAnimal } from '../hooks/useAnimals';
import { useApplications, useUpdateApplicationStatus } from '../hooks/useApplications';

export function StaffPage() {
  const [tab, setTab] = useState('applications');

  return (
    <section>
      <h2>Staff panel</h2>
      <div className="tabs">
        <button type="button" className={tab === 'applications' ? 'active' : ''} onClick={() => setTab('applications')}>
          Applications
        </button>
        <button type="button" className={tab === 'animals' ? 'active' : ''} onClick={() => setTab('animals')}>
          Animals
        </button>
      </div>
      {tab === 'applications' ? <ApplicationsTab /> : <AnimalsTab />}
    </section>
  );
}

export function ApplicationsTab() {
  const { data: applications, loading: appsLoading, error: appsError, refetch: refetchApplications } = useApplications();
  const { data: animals, loading: animalsLoading, refetch: refetchAnimals } = useAnimals();
  const updateStatus = useUpdateApplicationStatus();
  const [decidingId, setDecidingId] = useState(null);
  const [rowErrors, setRowErrors] = useState({});

  const animalsById = useMemo(() => {
    const map = new Map();
    for (const animal of animals ?? []) map.set(animal.id, animal);
    return map;
  }, [animals]);

  async function decide(application, status) {
    if (status === 'approved') {
      const confirmed = window.confirm(
        'Approving this application marks the animal as adopted and cannot be undone. Continue?'
      );
      if (!confirmed) return;
    }
    setDecidingId(application.id);
    setRowErrors((e) => ({ ...e, [application.id]: null }));
    try {
      await updateStatus.run(application.id, status);
      refetchApplications();
      refetchAnimals(); // approving/rejecting can flip the animal's status too
    } catch (err) {
      setRowErrors((e) => ({ ...e, [application.id]: err.message }));
    } finally {
      setDecidingId(null);
    }
  }

  if (appsLoading || animalsLoading) return <Spinner label="Loading applications…" />;
  if (appsError) return <p className="form-error">Could not load applications: {appsError}</p>;

  return (
    <div>
      {applications.length === 0 && <p className="empty-state">No applications yet. Check back soon!</p>}
      {applications.length > 0 && (
        <div className="table-scroll">
          <table className="applications-table">
            <thead>
              <tr>
                <th>Animal</th>
                <th>Adopter</th>
                <th>Status</th>
                <th>Submitted</th>
                <th>Decision</th>
              </tr>
            </thead>
            <tbody>
              {applications.map((application) => {
                const animal = animalsById.get(application.animal_id);
                const isPending = application.status === 'pending';
                const isDeciding = decidingId === application.id;
                return (
                  <tr key={application.id}>
                    <td>{animal ? `${animal.name} (${animal.species})` : `#${application.animal_id}`}</td>
                    <td>#{application.adopter_id}</td>
                    <td>
                      <span className={`status-badge status-${application.status}`}>{application.status}</span>
                    </td>
                    <td>{new Date(application.created_at).toLocaleDateString()}</td>
                    <td>
                      {isPending ? (
                        <div className="row-actions">
                          <button type="button" onClick={() => decide(application, 'approved')} disabled={isDeciding}>
                            Approve
                          </button>
                          <button
                            type="button"
                            className="btn-danger-outline"
                            onClick={() => decide(application, 'rejected')}
                            disabled={isDeciding}
                          >
                            Reject
                          </button>
                        </div>
                      ) : (
                        <span className="muted">Decided</span>
                      )}
                      {rowErrors[application.id] && <p className="form-error">{rowErrors[application.id]}</p>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function AnimalsTab() {
  const { data: animals, loading: animalsLoading, error: animalsError, refetch: refetchAnimals } = useAnimals();
  const { data: shelters, loading: sheltersLoading, error: sheltersError } = useShelters();
  const createAnimal = useCreateAnimal();
  const updateAnimal = useUpdateAnimal();
  const [showCreate, setShowCreate] = useState(false);
  const [editingId, setEditingId] = useState(null);

  async function handleCreate(values) {
    await createAnimal.run(values);
    setShowCreate(false);
    refetchAnimals();
  }

  async function handleUpdate(id, patch) {
    await updateAnimal.run(id, patch);
    setEditingId(null);
    refetchAnimals();
  }

  if (animalsLoading || sheltersLoading) return <Spinner label="Loading animals…" />;
  if (animalsError) return <p className="form-error">Could not load animals: {animalsError}</p>;
  if (sheltersError) return <p className="form-error">Could not load shelters: {sheltersError}</p>;

  return (
    <div>
      <div className="animals-tab-header">
        <button type="button" className="btn-secondary" onClick={() => setShowCreate((v) => !v)}>
          {showCreate ? 'Cancel' : 'Add animal'}
        </button>
      </div>
      {showCreate && (
        <AnimalForm mode="create" shelters={shelters} onSubmit={handleCreate} onCancel={() => setShowCreate(false)} />
      )}

      {animals.length === 0 && !showCreate && <p className="empty-state">No animals yet. Add the first one above!</p>}
      {animals.length > 0 && (
        <div className="table-scroll">
          <table className="applications-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Species</th>
                <th>Breed</th>
                <th>Age</th>
                <th>Status</th>
                <th>Shelter</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {animals.map((animal) =>
                editingId === animal.id ? (
                  <tr key={animal.id}>
                    <td colSpan={7}>
                      <AnimalForm
                        mode="edit"
                        animal={animal}
                        shelters={shelters}
                        onSubmit={(patch) => handleUpdate(animal.id, patch)}
                        onCancel={() => setEditingId(null)}
                      />
                    </td>
                  </tr>
                ) : (
                  <tr key={animal.id}>
                    <td>{animal.name}</td>
                    <td>{animal.species}</td>
                    <td>{animal.breed}</td>
                    <td>{animal.age}</td>
                    <td>
                      <span className={`status-badge status-${animal.status}`}>{animal.status}</span>
                    </td>
                    <td>{shelters.find((s) => s.id === animal.shelter_id)?.name ?? animal.shelter_id}</td>
                    <td>
                      <button type="button" className="btn-secondary" onClick={() => setEditingId(animal.id)}>
                        Edit
                      </button>
                    </td>
                  </tr>
                )
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
