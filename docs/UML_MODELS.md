# UML — Model Layer

Class diagram of the ShelterHub domain model
([`backend/app/models.py`](../backend/app/models.py)). Rendered by GitHub
automatically; also viewable at [mermaid.live](https://mermaid.live).

```mermaid
classDiagram
    direction TB

    class User {
        <<abstract>>
        +int id
        +str email
        +str hashed_password
        +str role
        +datetime created_at
        +is_staff() bool
        +is_adopter() bool
    }

    class Staff {
        +int shelter_id
        +Shelter shelter
    }

    class Adopter {
        +list~ShelterApplication~ applications
        +has_open_application_for(animal_id) bool
    }

    class Shelter {
        +int id
        +str name
        +str city
        +datetime created_at
        +list~Animal~ animals
        +list~Staff~ staff
        +available_animals() list~Animal~
    }

    class Animal {
        +int id
        +str name
        +str species
        +str breed
        +int age
        +AnimalStatus status
        +int shelter_id
        +datetime created_at
        +Shelter shelter
        +list~ShelterApplication~ applications
        +is_available() bool
        +open_applications() list~ShelterApplication~
    }

    class ShelterApplication {
        +int id
        +int adopter_id
        +int animal_id
        +ApplicationStatus status
        +datetime created_at
        +Adopter adopter
        +Animal animal
        +is_open() bool
    }

    class UserRole {
        <<enumeration>>
        ADOPTER
        STAFF
    }

    class AnimalStatus {
        <<enumeration>>
        AVAILABLE
        PENDING
        ADOPTED
    }

    class ApplicationStatus {
        <<enumeration>>
        PENDING
        APPROVED
        REJECTED
    }

    User <|-- Staff : single-table inheritance
    User <|-- Adopter : single-table inheritance

    Shelter "1" o-- "0..*" Animal : houses
    Shelter "1" o-- "0..*" Staff : employs
    Adopter "1" o-- "0..*" ShelterApplication : submits
    Animal "1" o-- "0..*" ShelterApplication : receives

    Animal ..> AnimalStatus : status
    ShelterApplication ..> ApplicationStatus : status
    User ..> UserRole : role
```

## Inheritance mapping

`User`, `Staff` and `Adopter` share a **single `users` table**
(SQLAlchemy single-table inheritance). The discriminator is `users.role`, which
is the very same `role` field that `POST /auth/register` accepts and returns —
so the persistence layer and the public API cannot drift apart.

```
users
├── id, email, hashed_password, role, created_at   -- declared on User
└── shelter_id                                     -- declared on Staff, NULL for adopters
```

`User` declares no `polymorphic_identity`, so it is abstract in practice: every
row is a `Staff` or an `Adopter`. Querying `select(User)` returns both subtypes
as their concrete Python classes; `select(Adopter)` is automatically filtered to
`role = 'adopter'`.

`Staff.shelter_id` is nullable — the registration contract accepts no shelter,
and single-table inheritance requires subtype columns to be nullable since they
are shared with the other subtype.

## Status lifecycles

```mermaid
stateDiagram-v2
    direction LR
    [*] --> available : POST /animals
    available --> pending : first application submitted
    pending --> pending : a competing application is submitted
    pending --> adopted : staff approve an application
    pending --> available : last open application rejected
    note right of adopted
        Staff may also set any status
        directly via PATCH /animals/{id}
    end note
```

```mermaid
stateDiagram-v2
    direction LR
    [*] --> pending : POST /applications
    pending --> approved : PATCH /applications/{id}
    pending --> rejected : PATCH /applications/{id}
    pending --> rejected : a competing application was approved
```

Transitions marked on the animal diagram that are **not** spelled out in
[API_CONTRACT.md](API_CONTRACT.md) are recorded in
[BACKEND_DECISIONS.md](BACKEND_DECISIONS.md).
