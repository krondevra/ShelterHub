# API Contract — ShelterHub

## Auth
POST /auth/register
Body: { "email": str, "password": str, "role": "adopter" | "staff" }
Response 201: { "id": int, "email": str, "role": str }

POST /auth/login
Body: { "email": str, "password": str }
Response 200: { "access_token": str, "token_type": "bearer" }

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
Body: partial fields to update
Response 200: updated Animal object

## Applications
POST /applications   (adopter only)
Body: { "animal_id": int }
Response 201: { "id": int, "adopter_id": int, "animal_id": int,
  "status": "pending", "created_at": str }

GET /applications   (staff: all, adopter: only own)
Response 200: [ same object as above ]

PATCH /applications/{id}   (staff only)
Body: { "status": "approved" | "rejected" }
Response 200: updated Application object
(on "approved" -> backend auto-sets Animal.status = "adopted")

## Errors
{ "detail": str }   — standard FastAPI error format, used for 4xx/5xx responses
