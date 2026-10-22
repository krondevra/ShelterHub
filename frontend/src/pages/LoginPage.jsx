import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { loginSchema } from '../validation/authSchemas';
import { validate } from '../validation/validate';

export function LoginPage() {
  const { login, loginLoading, loginError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname ?? '/';

  const [form, setForm] = useState({ email: '', password: '' });
  const [fieldErrors, setFieldErrors] = useState({});

  function update(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const { values, errors } = validate(loginSchema, form);
    setFieldErrors(errors);
    if (!values) return;
    try {
      await login(values);
      navigate(from, { replace: true });
    } catch {
      // loginError from context already carries the message
    }
  }

  return (
    <section className="auth-page">
      <h2>Log in</h2>
      <form onSubmit={handleSubmit} noValidate>
        <label>
          Email
          <input type="email" value={form.email} onChange={update('email')} />
        </label>
        {fieldErrors.email && <p className="form-error">{fieldErrors.email}</p>}

        <label>
          Password
          <input type="password" value={form.password} onChange={update('password')} />
        </label>
        {fieldErrors.password && <p className="form-error">{fieldErrors.password}</p>}

        {loginError && <p className="form-error">{loginError}</p>}

        <button type="submit" disabled={loginLoading}>
          {loginLoading ? 'Logging in…' : 'Log in'}
        </button>
      </form>
    </section>
  );
}
