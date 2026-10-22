import { useMemo } from 'react';
import { Spinner } from '../components/Spinner';
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

  if (appsLoading || animalsLoading) return <Spinner label="Loading your applications…" />;
  if (appsError) return <p className="form-error">Could not load applications: {appsError}</p>;

  return (
    <section>
      <h2>My applications</h2>
      {applications.length === 0 && (
        <p className="empty-state">No applications yet. Browse the animals and apply to adopt one!</p>
      )}
      {applications.length > 0 && (
        <div className="table-scroll">
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
        </div>
      )}
    </section>
  );
}
