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
* Reference data management for **Genres** and **Platforms**

## Catalog Module

The catalog module provides reference entities used across the platform.

### Entities
* **Genre** – Game categories (e.g., RPG, Action)
* **Platform** – Supported platforms (e.g., PC, Console)

### API Access Rules
* **Read access**: Public
* **Write access**: Admin-only

### Design Notes
* UUID primary keys
* Case-insensitive, normalized unique names
* Admin-managed reference data
* Exposed via DRF `ModelViewSet` and routers

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

Core authentication, user management, API infrastructure, and catalog reference data are complete. Game-related domain features will be added next.
