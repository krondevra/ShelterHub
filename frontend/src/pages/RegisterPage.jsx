import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { registerSchema } from '../validation/authSchemas';
import { validate } from '../validation/validate';

export function RegisterPage() {
  const { register, registerLoading, registerError } = useAuth();
  const [form, setForm] = useState({ email: '', password: '', role: 'adopter' });
  const [fieldErrors, setFieldErrors] = useState({});
  const [done, setDone] = useState(false);

  function update(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const { values, errors } = validate(registerSchema, form);
    setFieldErrors(errors);
    if (!values) return;
    try {
      await register(values);
      setDone(true);
    } catch {
      // registerError from context already carries the message (e.g. 409 email taken)
    }
  }

  if (done) {
    return (
      <section className="auth-page">
        <h2>Account created</h2>
        <p>
          You can now <Link to="/login">log in</Link>.
        </p>
      </section>
    );
  }

  return (
    <section className="auth-page">
      <h2>Register</h2>
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

        <label>
          I am a
          <select value={form.role} onChange={update('role')}>
            <option value="adopter">Adopter</option>
            <option value="staff">Staff</option>
          </select>
        </label>
        {fieldErrors.role && <p className="form-error">{fieldErrors.role}</p>}

        {registerError && <p className="form-error">{registerError}</p>}

        <button type="submit" disabled={registerLoading}>
          {registerLoading ? 'Creating account…' : 'Register'}
        </button>
      </form>
    </section>
  );
}
