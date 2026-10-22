# API Contract — ShelterHub

Authenticated routes take `Authorization: Bearer <access_token>` (from /auth/login).
Routes with no role noted are public.

## Auth
POST /auth/register
Body: { "email": str, "password": str (8-72 chars, max 72 bytes UTF-8), "role": "adopter" | "staff" }
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
    "status": "available" | "pending" | "adopted", "shelter_id": int,
    "photo_url": str | null }
]
(photo_url is a path relative to the API base URL, e.g. "/uploads/animals/7.jpg",
null when the animal has no photo)

GET /animals/{id}
Response 200: same object as above

POST /animals   (staff only)
Body: { "name": str, "species": str, "breed": str, "age": int, "shelter_id": int }
Response 201: full Animal object (status defaults to "available")

PATCH /animals/{id}   (staff only)
Body: any subset of { "name", "species", "breed", "age", "shelter_id" }
Response 200: updated Animal object
(status cannot be set here — it is driven only by the application flow below)
(photo_url cannot be set on POST or PATCH either — 422; use the photo routes below)

POST /animals/{id}/photo   (staff only)
Body: multipart/form-data, one field "file" — JPEG, PNG or WebP, max 5 MB
Response 200: updated Animal object (photo_url set)
- uploading again replaces the previous photo
- 404 unknown animal · 413 file over 5 MB · 415 not JPEG/PNG/WebP

DELETE /animals/{id}/photo   (staff only)
Response 200: updated Animal object (photo_url null)
- 404 unknown animal (no error if the animal has no photo)

GET /uploads/animals/{file}
Serves the stored image file (public)

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
422 is the exception: "detail" is a list of validation errors,
{ "detail": [ { "loc": [str | int], "msg": str, "type": str } ] }
401 missing/invalid/expired token · 403 wrong role · 404 unknown id ·
409 conflict (see above) · 413 upload too large · 415 unsupported file type ·
422 invalid body
