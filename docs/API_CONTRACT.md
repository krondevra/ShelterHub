# API Contract — ShelterHub

Authenticated routes take `Authorization: Bearer <access_token>` (from /auth/login).
Routes with no role noted are public.

## Auth
POST /auth/register
Body: { "email": str, "password": str (8-72 chars), "role": "adopter" | "staff" }
Response 201: { "id": int, "email": str, "role": str }
409 if the email is already registered

POST /auth/login
Body: { "email": str, "password": str }
Response 200: { "access_token": str, "token_type": "bearer" }
401 on wrong email or password

## Shelters
GET /shelters
Response 200: [ { "id": int, "name": str, "city": str | null } ]
(read-only; shelters are seeded, used to pick a shelter_id for POST /animals)

## Animals
GET /animals
Response 200: [
  { "id": int, "name": str, "species": str, "breed": str, "age": int,
    "status": "available" | "pending" | "adopted", "shelter_id": int }
]

GET /animals/{id}
Response 200: same object as above

POST /animals   (staff only)
Body: { "name": str, "species": str, "breed": str, "age": int, "shelter_id": int }
Response 201: full Animal object (status defaults to "available")

PATCH /animals/{id}   (staff only)
Body: any subset of { "name", "species", "breed", "age", "shelter_id" }
Response 200: updated Animal object
(status cannot be set here — it is driven only by the application flow below)

## Applications
POST /applications   (adopter only)
Body: { "animal_id": int }
Response 201: { "id": int, "adopter_id": int, "animal_id": int,
  "status": "pending", "created_at": str }
- animal "available" -> becomes "pending"
- animal "pending" -> allowed, several adopters may apply for the same animal
- 409 if the animal is "adopted", or this adopter already has a pending
  application for it

GET /applications   (staff: all, adopter: only own)
Response 200: [ same object as above ]

PATCH /applications/{id}   (staff only)
Body: { "status": "approved" | "rejected" }
Response 200: updated Application object
- "approved" -> Animal.status = "adopted", other pending applications for
  that animal are set to "rejected"
- "rejected" -> if no other pending application remains, Animal.status goes
  back to "available"
- 409 if the application is already approved/rejected

## Errors
{ "detail": str }   — standard FastAPI error format, used for 4xx/5xx responses
401 missing/invalid/expired token · 403 wrong role · 404 unknown id ·
409 conflict (see above) · 422 invalid body
