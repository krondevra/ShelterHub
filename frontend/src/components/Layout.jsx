import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

function navLinkClass({ isActive }) {
  return isActive ? 'active' : undefined;
}

export function Layout() {
  const { isAuthenticated, user, logout } = useAuth();

  return (
    <div className="app">
      <header className="app-header">
        <nav className="app-nav">
          <NavLink to="/" end className="app-brand">
            ShelterHub
          </NavLink>
          <div className="app-nav-links">
            <NavLink to="/" end className={navLinkClass}>
              Animals
            </NavLink>
            {isAuthenticated && user.role === 'adopter' && (
              <NavLink to="/applications" className={navLinkClass}>
                My applications
              </NavLink>
            )}
            {isAuthenticated && user.role === 'staff' && (
              <NavLink to="/staff" className={navLinkClass}>
                Staff panel
              </NavLink>
            )}
          </div>
          <div className="app-nav-auth">
            {isAuthenticated ? (
              <>
                <span className={`role-badge role-badge-${user.role}`}>{user.role}</span>
                <button type="button" className="btn-secondary" onClick={logout}>
                  Log out
                </button>
              </>
            ) : (
              <>
                <NavLink to="/login" className={navLinkClass}>
                  Log in
                </NavLink>
                <NavLink to="/register" className={navLinkClass}>
                  Register
                </NavLink>
              </>
            )}
          </div>
        </nav>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
