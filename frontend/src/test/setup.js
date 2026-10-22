import '@testing-library/jest-dom/vitest';

// jsdom's own localStorage can end up shadowed by Node's experimental native
// implementation (gated behind --localstorage-file) depending on Node/jsdom
// version pairing, leaving `window.localStorage` undefined under Vitest. A
// small in-memory polyfill sidesteps the whole engine-pairing question.
if (typeof window !== 'undefined' && !window.localStorage) {
  const store = new Map();
  const localStoragePolyfill = {
    getItem: (key) => (store.has(key) ? store.get(key) : null),
    setItem: (key, value) => store.set(key, String(value)),
    removeItem: (key) => store.delete(key),
    clear: () => store.clear(),
    key: (index) => Array.from(store.keys())[index] ?? null,
    get length() {
      return store.size;
    },
  };
  Object.defineProperty(window, 'localStorage', {
    value: localStoragePolyfill,
    writable: true,
    configurable: true,
  });
}
