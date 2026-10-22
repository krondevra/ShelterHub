// Extra per-shelter content not provided by the backend (GET /shelters only
// returns { id, name, city }). Shelters are seeded server-side and not
// editable through the UI, so keying by name here is safe — but this is
// placeholder text: edit it to describe your actual shelters.
export const SHELTER_INFO = {
  'Paws Haven': {
    country: 'Latvia',
    description: 'Our longest-running partner shelter, focused on dogs and cats surrendered by local families.',
  },
  'Second Chance Shelter': {
    country: 'Lithuania',
    description: 'A no-kill shelter working closely with local vets to rehabilitate rescued strays.',
  },
  'Happy Tails Rescue': {
    country: 'Estonia',
    description: 'Specializes in finding homes for senior and special-needs animals.',
  },
};
