import { useMemo } from 'react';
import { useAnimals } from '../hooks/useAnimals';
import { useApplications } from '../hooks/useApplications';

export function ApplicationsPage() {
  const { data: applications, loading: appsLoading, error: appsError } = useApplications();
  const { data: animals, loading: animalsLoading } = useAnimals();

  const animalsById = useMemo(() => {
    const map = new Map();
    for (const animal of animals ?? []) map.set(animal.id, animal);
    return map;
  }, [animals]);

  if (appsLoading || animalsLoading) return <p>Loading your applications…</p>;
  if (appsError) return <p className="form-error">Could not load applications: {appsError}</p>;

  return (
    <section>
      <h2>My applications</h2>
      {applications.length === 0 && <p>You haven't applied for any animals yet.</p>}
      {applications.length > 0 && (
        <table className="applications-table">
          <thead>
            <tr>
              <th>Animal</th>
              <th>Status</th>
              <th>Submitted</th>
            </tr>
          </thead>
          <tbody>
            {applications.map((application) => {
              const animal = animalsById.get(application.animal_id);
              return (
                <tr key={application.id}>
                  <td>{animal ? `${animal.name} (${animal.species})` : `#${application.animal_id}`}</td>
                  <td>
                    <span className={`status-badge status-${application.status}`}>{application.status}</span>
                  </td>
                  <td>{new Date(application.created_at).toLocaleDateString()}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </section>
  );
}
