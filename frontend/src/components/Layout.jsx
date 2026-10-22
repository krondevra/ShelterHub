import { Link, Outlet } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export function Layout() {
  const { isAuthenticated, user, logout } = useAuth();

  return (
    <div className="app">
      <header className="app-header">
        <nav className="app-nav">
          <Link to="/" className="app-brand">
            ShelterHub
          </Link>
          <div className="app-nav-links">
            <Link to="/">Animals</Link>
            {isAuthenticated && user.role === 'adopter' && <Link to="/applications">My applications</Link>}
            {isAuthenticated && user.role === 'staff' && <Link to="/staff">Staff panel</Link>}
          </div>
          <div className="app-nav-auth">
            {isAuthenticated ? (
              <>
                <span className="app-user">{user.role}</span>
                <button type="button" onClick={logout}>
                  Log out
                </button>
              </>
            ) : (
              <>
                <Link to="/login">Log in</Link>
                <Link to="/register">Register</Link>
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
