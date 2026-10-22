import { Navigate, Route, Routes } from 'react-router-dom';
import { Layout } from './components/Layout';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AnimalsPage } from './pages/AnimalsPage';
import { ApplicationsPage } from './pages/ApplicationsPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { StaffPage } from './pages/StaffPage';

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<AnimalsPage />} />
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />
        <Route element={<ProtectedRoute roles={['adopter']} />}>
          <Route path="applications" element={<ApplicationsPage />} />
        </Route>
        <Route element={<ProtectedRoute roles={['staff']} />}>
          <Route path="staff" element={<StaffPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

export default App;
