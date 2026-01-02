# GamerHouse

GamerHouse is a **Django REST Framework (DRF)** backend for managing a personal game library. It focuses on a clean, secure, and consistent API foundation that can scale into a full gaming platform.

## Features

* Custom **User model** with UUID primary keys
* **Role-based access control** (Admin / Gamer)
* **Soft delete** support with active/all user managers
* JWT authentication using **SimpleJWT**
* Refresh-token logout with token blacklisting
* Standardized API responses and pagination
* Global exception handling with semantic HTTP status codes

## Tech Stack

* Python
* Django
* Django REST Framework

## API Conventions

### Success Response

```json
{ "data": { ... } }
```
### Paginated Response

```json
{
  "count": 42,
  "page": 1,
  "page_size": 10,
  "next": "...",
  "previous": null,
  "data": [ ... ]
}
```

### Error Response

```json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid request data",
    "details": { ... }
  }
}
```

## Status

Core authentication, user management, and API infrastructure are in place. Game-related domain features will be added next.
