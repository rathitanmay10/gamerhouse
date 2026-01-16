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
* **Game** – A user-owned game entry with status, rating, and playtime

### API Access Rules
* **Read access**: All users
* **Write access**: Admin-only

### Design Notes
* UUID primary keys
* Case-insensitive, normalized unique names
* Admin-managed reference data
* Exposed via DRF `ModelViewSet` and routers

## UserGames Module

The user games module allows users to manage their personal game library with progress tracking and metadata.

### Entity
* **UserGame** – A user-owned game entry with status, rating, and playtime

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
* PostgreSQL
* SimpleJWT 

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
  "error": { ... }
}
```
## Project Setup

### 1. Clone the repository
```bash
git clone https://github.com/tanmayrathi-gkmit/gamerhouse.git
cd gamerhouse
```

### Install uv if not present
``` bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Create virtual environment & install dependencies
```bash
uv venv
source .venv/bin/activate
uv sync
```
### Environment variables
Copy the example environment file and Update values as needed.

`.env.example`
```
# Django settings
SECRET_KEY=secret_key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Database configuration (PostgreSQL)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=database_name
DB_USER=user
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432
```
> `SECRET_KEY` must be changed for any non-local environment.

### Database Setup
Ensure PostgreSQL is running and the database exists:
```
createdb database_name
```
Apply migrations:
```
python manage.py migrate
```

### Seeding Base Data (Required)
Run the seed command to create essential data:
```
python manage.py seed_db
```

**Seeded data**

* Admin user
* Game genres
* Supported platforms

**Default admin credentials**
Email:    admin@gamerhouse.dev
Username: admin
Password: admin

> Change this password immediately after first login.

### Running the Server
```
python manage.py runserver
```
## Status

Core authentication, user management, API infrastructure, catalog reference data,
and game library management are complete.

