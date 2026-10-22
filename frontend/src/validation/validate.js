// Runs a Zod schema and returns { values, errors } instead of throwing,
// so form components can render field-level messages.
export function validate(schema, data) {
  const result = schema.safeParse(data);
  if (result.success) return { values: result.data, errors: {} };

  const errors = {};
  for (const issue of result.error.issues) {
    const field = issue.path[0];
    if (field && !errors[field]) errors[field] = issue.message;
  }
  return { values: null, errors };
}
