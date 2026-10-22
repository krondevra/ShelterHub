// Exported so callers can build an absolute URL for a relative path the API
// returns (e.g. an animal's photo_url).
export const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
const TOKEN_KEY = 'shelterhub_token';

// `window.localStorage`, not the bare global: Node 20.11+/22+ defines its own
// experimental `localStorage` global that otherwise shadows jsdom's in tests.
export const tokenStorage = {
  get: () => window.localStorage.getItem(TOKEN_KEY),
  set: (token) => window.localStorage.setItem(TOKEN_KEY, token),
  clear: () => window.localStorage.removeItem(TOKEN_KEY),
};

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

let onUnauthorized = null;
export function setUnauthorizedHandler(fn) {
  onUnauthorized = fn;
}

// FastAPI: 401/403/404/409 send `detail` as a string; 422 sends a list of
// { loc, msg, type } validation errors instead.
function formatDetail(detail) {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => d.msg).join('; ');
  }
  return null;
}

export async function request(path, { method = 'GET', body, auth = true } = {}) {
  // FormData (file uploads): let the browser set its own multipart boundary
  // in Content-Type, and send the FormData as-is instead of JSON-encoding it.
  const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;

  const headers = {};
  if (body !== undefined && !isFormData) headers['Content-Type'] = 'application/json';
  const token = tokenStorage.get();
  if (auth && token) headers.Authorization = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : isFormData ? body : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, 'Could not reach the server. Is the backend running?');
  }

  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);

  if (!res.ok) {
    if (res.status === 401 && auth && token) onUnauthorized?.();
    throw new ApiError(res.status, formatDetail(data?.detail) ?? `Request failed (${res.status})`);
  }
  return data;
}

export const api = {
  get: (path, opts) => request(path, { ...opts, method: 'GET' }),
  post: (path, body, opts) => request(path, { ...opts, method: 'POST', body }),
  patch: (path, body, opts) => request(path, { ...opts, method: 'PATCH', body }),
  delete: (path, opts) => request(path, { ...opts, method: 'DELETE' }),
  // `formData` must be a FormData instance; see the isFormData check in request().
  upload: (path, formData, opts) => request(path, { ...opts, method: 'POST', body: formData }),
};
