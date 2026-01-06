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
* Personal **Game library management**
* Game progress tracking (wishlist, playing, completed, dropped)
* Role-aware access (admin visibility, user ownership)
* Query-based filtering for game lists

## Catalog Module

The catalog module provides reference entities used across the platform.

### Entities
* **Genre** – Game categories (e.g., RPG, Action)
* **Platform** – Supported platforms (e.g., PC, Console)

### API Access Rules
* **Read access**: All users
* **Write access**: Admin-only

### Design Notes
* UUID primary keys
* Case-insensitive, normalized unique names
* Admin-managed reference data
* Exposed via DRF `ModelViewSet` and routers

## Games Module

The games module allows users to manage their personal game library with progress tracking and metadata.

### Entity
* **Game** – A user-owned game entry with status, rating, and playtime

### Core Capabilities
* Create, update, soft-delete personal game entries
* Track progress using status (wishlist, playing, completed, dropped)
* Optional metadata: hours played, personal rating, notes
* Automatic completion date handling
* Query filtering by title, status, genre, platform, rating, and hours played

### API Access Rules
* **Admin**
  * Read-only access
  * Can view all non-deleted games
* **Gamer**
  * Full CRUD access
  * Restricted to own games only

### Design Notes
* UUID primary keys
* Soft deletion using `deleted_at`
* Indexed for user + status and creation time
* Exposed via DRF `ModelViewSet` and router

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

Core authentication, user management, API infrastructure, catalog reference data,
and game library management are complete.

