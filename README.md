# GamerHouse

GamerHouse is a **multi-tenant Django REST Framework (DRF)** backend for managing game libraries across multiple organizations. It provides a secure, scalable platform with role-based access control, email verification, and background task processing.

## Features

### Core Architecture
* **Multi-tenancy** – Complete data isolation between organizations
* **UUID primary keys** – All models use UUIDs for security and scalability
* **Soft delete** support with active/all object managers
* **Background tasks** – Celery with Redis for async processing
* **Caching** – Redis-backed Django cache with decorator-based response caching
* **Response filtering** – Search and filter support for catalog endpoints
* **Rate limiting** – Authentication endpoints protected with rate limiting (5/minute)

### Authentication & Authorization
* **Email-based authentication** – Login with email instead of username
* **Email verification** – Required for new user registrations
* **OTP login flow** – Two-step authentication with OTP verification
* **Password reset** – Forgot password and reset password endpoints
* **JWT tokens** – Using SimpleJWT with token blacklisting
* **Role-based access control** – Super Admin, Admin, and Gamer roles

### Game Management
* **Tenant-scoped games** – Games are managed per tenant
* **Personal game library** – Track your gaming progress
* **Status tracking** – Wishlist, Playing, Completed, Dropped
* **Advanced filtering** – Filter by status, platform, rating, hours played, genre
* **Game notes** – Add personal notes to your games
* **Free tier limits** – Max 5 games for free users

### Payments & Subscriptions
* **Razorpay integration** – Secure payment gateway integration
* **Premium subscriptions** – Unlock unlimited game library entries
* **Subscription management** – Track subscription status and billing
* **Payment verification** – Secure signature verification for payments
* **Webhook handling** – Automatic payment status updates via webhooks
* **Payment polling** – Automatic reconciliation of pending payments

### Logging & Observability
* **Structured JSON logging** – JSON-formatted logs for easier parsing and analysis
* **Configurable logging** – File, console, and log level configuration
* **Request/Response logging** – Track all API requests and responses
* **Correlation IDs** – Trace requests across distributed systems using context variables
* **Task logging** – Background task execution tracking

### Error Handling
* **Standardized error responses** – Consistent error format across all endpoints
* **Detailed error messages** – Clear, actionable error descriptions
* **Proper HTTP status codes** – Correct status codes for different error types
* **Middleware-based error handling** – JSON error formatting and logging

## Architecture Overview

### Multi-Tenancy
GamerHouse uses a **shared database, shared schema** multi-tenancy model where:
- All data is scoped to a tenant via foreign keys
- Users belong to a single tenant
- Admins can only manage users and games within their tenant
- Super admins can manage platform-wide resources
- **Automatic tenant context isolation** – Tenant is automatically set during authentication and used for query filtering
- **Context variables** – Tenant context is safely stored per request using Python's `contextvars` for async compatibility

### Role Hierarchy
1. **Super Admin** – Platform-level administration, manages catalog (games, genres, platforms), payments, and subscriptions
2. **Admin** – Tenant-level administration, manages users and games within their tenant, handles premium subscriptions
3. **Gamer** – Regular user, manages their own game library (limited to 5 games on free tier)

## Modules

### Tenants Module
Manages organizations and tenant isolation.

**Entities:**
* **Tenant** – Organization with status (active/inactive)

**API Access:**
* Super Admin: Full access
* Admin: Read-only access to own tenant

### Catalog Module
Platform-wide reference data for games, genres, and platforms with response caching.

**Entities:**
* **Genre** – Game categories (e.g., RPG, Action, Strategy)
* **Platform** – Gaming platforms (e.g., PC, PlayStation, Xbox)
* **Game** – Master game catalog

**Features:**
* Search by title (Games)
* Filter by genre and platform (Games)
* Search by name (Genres and Platforms)
* Response caching with automatic invalidation on mutations

**API Access:**
* Super Admin: Full CRUD access
* Admin: Read-only access
* Gamer: No access

### Tenant Games Module
Tenant-specific game instances linked to the master catalog.

**Entities:**
* **TenantGame** – Links a catalog game to a tenant

**API Access:**
* Admin: Full CRUD access within their tenant
* Gamer: Read-only access within their tenant

### User Games Module
Personal game library management with progress tracking.

**Entities:**
* **UserGame** – User's personal game entry with status, rating, playtime
* **UserGameNote** – Personal notes for games

**Features:**
* Track game status (wishlist, playing, completed, dropped)
* Record hours played (max 100,000)
* Personal rating system
* Start and completion date tracking
* Platform-specific game entries
* Free tier limit: 5 games max
* Premium tier: Unlimited games

**API Access:**
* Admin: Full CRUD access for all users in their tenant
* Gamer: Full CRUD access for their own games only

### Payments Module
Handles payment processing and subscription management using Razorpay.

**Entities:**
* **Payment** – Records payment transactions with Razorpay integration
* **Subscription** – Tracks tenant premium subscription status
* **WebhookEvent** – Stores and processes payment webhooks

**Features:**
* Create payment orders via Razorpay
* Verify payment signatures for security
* Track payment lifecycle (created → paid → verified → activated)
* Automatic webhook processing for payment status updates
* Polling reconciliation for pending payments (every 15 minutes)
* Subscription status management (pending, active, expired)

**API Access:**
* Admin: Create and manage subscriptions for their tenant
* Super Admin: View all payments and subscriptions

## Tech Stack

* **Python 3.13+**
* **Django 6.0**
* **Django REST Framework 3.16+**
* **PostgreSQL** – Primary database
* **Redis** – Caching and message broker
* **Celery** – Background task processing
* **SimpleJWT** – JWT authentication
* **django-filter** – Advanced filtering
* **django-celery-beat** – Periodic task scheduling
* **Razorpay SDK** – Payment gateway integration

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
  "error": "Error message describing what went wrong"
}
```

### Response Caching
Catalog endpoints (Genres, Platforms, Games) implement automatic response caching:
- GET requests are cached for 2 minutes
- Cache is automatically invalidated on POST, PATCH, DELETE operations
- Cache keys include full query parameters for accurate filtering

### Rate Limiting
Authentication endpoints are protected with rate limiting:
- Auth endpoints: 5 requests per minute per IP

### Logging
All API requests and responses are logged with the following information:
- Request method, path, and parameters
- Response status and latency
- Correlation ID for request tracing
- User and tenant information

Logs are available in both:
- **Console output** – For development
- **File output** – Stored in `logs/` directory for production

## Project Setup

### Prerequisites
* Python 3.13 or higher
* PostgreSQL 12 or higher
* Redis 6 or higher
* SMTP server (for email verification)
* Razorpay account (for payment processing)

### 1. Clone the repository
```bash
git clone https://github.com/tanmayrathi-gkmit/gamerhouse.git
cd gamerhouse
```

### 2. Install uv (if not present)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Create virtual environment & install dependencies
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync
```

### 4. Environment Variables
Copy the example environment file and update values as needed.

`.env.example`
```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Database Configuration (PostgreSQL)
POSTGRES_NAME=gamerhouse_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Celery & Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/2
CELERY_TASK_TIME_LIMIT=30
CELERY_TASK_SOFT_TIME_LIMIT=25
CELERY_RESULT_EXPIRES=3600

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@gamerhouse.dev

# Frontend URL (for email links)
FRONTEND_URL=http://localhost:8000/

# Razorpay Payment Gateway (Sandbox)
RAZORPAY_KEY_ID=rzp_test_your_key_id_here
RAZORPAY_KEY_SECRET=your_key_secret_here
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret_here

# Logging Configuration (Optional)
LOG_LEVEL=INFO
LOG_FILE_ENABLED=True
LOG_CONSOLE_ENABLED=True
```

> **Security Note:** `SECRET_KEY` must be changed for any non-local environment. Use real Razorpay keys in production.

### 5. Database Setup
Ensure PostgreSQL is running and create the database:
```bash
createdb gamerhouse_db
```

Apply migrations:
```bash
python manage.py migrate
```

### 6. Seed Base Data (Required)
Run the seed command to create essential data:
```bash
python manage.py seed_db
```

**Seeded data:**
* Super Admin user
* Game genres (RPG, Action, Strategy, etc.)
* Gaming platforms (PC, PlayStation, Xbox, etc.)

**Default Super Admin Credentials:**
```
Email:    super_admin@mailinator.com
Username: super_admin
Password: admin
```

> **Important:** Change this password immediately after first login.

### 7. Start Redis Server
```bash
redis-server
```

### 8. Start Celery Worker (in a new terminal)
```bash
celery -A gamer_house worker -l info
```

### 9. Start Celery Beat (in a new terminal, optional)
```bash
celery -A gamer_house beat -l info
```

### 10. Run the Development Server
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/v1/`

## API Endpoints

### Authentication
* `POST /api/v1/auth/tenant/<tenant_id>/register/` – Register new user
* `POST /api/v1/auth/verify-email/` – Verify email address
* `POST /api/v1/auth/resend-verification/` – Resend verification email
* `POST /api/v1/auth/login/` – Login (sends OTP)
* `POST /api/v1/auth/verify-login/` – Verify OTP and get tokens
* `POST /api/v1/auth/resend-login-otp/` – Resend login OTP
* `POST /api/v1/auth/refresh/` – Refresh access token
* `POST /api/v1/auth/logout/` – Logout (blacklist token)
* `POST /api/v1/auth/forgot-password/` – Request password reset
* `POST /api/v1/auth/reset-password/` – Reset password with token

### User Management
* `GET /api/v1/users/me/` – Get current user profile
* `PATCH /api/v1/users/me/` – Update current user profile
* `POST /api/v1/users/me/change-password/` – Change password
* `GET /api/v1/users/` – List users (Admin/Super Admin only)
* `GET /api/v1/users/<id>/` – Get user details
* `PATCH /api/v1/users/<id>/` – Update user
* `DELETE /api/v1/users/<id>/` – Soft delete user

### Catalog (Super Admin only for write)
* `GET /api/v1/genres/` – List genres (with search)
* `POST /api/v1/genres/` – Create genre
* `GET /api/v1/platforms/` – List platforms (with search)
* `POST /api/v1/platforms/` – Create platform
* `GET /api/v1/games/` – List games (with search, genre/platform filters)
* `POST /api/v1/games/` – Create game

**Catalog Query Parameters:**
* `search` – Search by name (Genres, Platforms) or title (Games)
* `genre` – Filter games by genre UUIDs (comma-separated)
* `platforms` – Filter games by platform UUIDs (comma-separated)

### Tenant Games
* `GET /api/v1/tenant-games/` – List tenant games
* `POST /api/v1/tenant-games/` – Add game to tenant
* `PATCH /api/v1/tenant-games/<id>/` – Update tenant game
* `DELETE /api/v1/tenant-games/<id>/` – Remove from tenant
* `POST /api/v1/tenant-games/bulk-add/` – Bulk add games by IDs, platforms, or genres
* `POST /api/v1/tenant-games/bulk-delete/` – Bulk remove multiple games from tenant

**Bulk Add Request:**
```json
{
  "games": ["uuid1", "uuid2"],
  "platforms": ["platform-uuid"],
  "genres": ["genre-uuid"],
  "exclude_games": ["uuid3"]
}
```

**Bulk Delete Request:**
```json
{
  "tenant_games": ["tenant-game-uuid1", "tenant-game-uuid2"]
}
```

### User Games
* `GET /api/v1/user-games/` – List user games (with filters)
* `POST /api/v1/user-games/` – Add game to library
* `GET /api/v1/user-games/<id>/` – Get game details
* `PATCH /api/v1/user-games/<id>/` – Update game
* `DELETE /api/v1/user-games/<id>/` – Remove from library

**Query Parameters:**
* `status` – Filter by status (wishlist, playing, completed, dropped)
* `platform` – Filter by platform UUID
* `min_hours_played` – Minimum hours played
* `min_rating` – Minimum personal rating

### User Game Notes
* `GET /api/v1/user-games/<game_id>/notes/` – List notes
* `POST /api/v1/user-games/<game_id>/notes/` – Create note
* `PATCH /api/v1/user-games/<game_id>/notes/<id>/` – Update note
* `DELETE /api/v1/user-games/<game_id>/notes/<id>/` – Delete note

### Payments
* `POST /api/v1/payments/create-order/` – Create Razorpay payment order (Admin only)
* `POST /api/v1/payments/verify/` – Verify payment signature (Admin only)
* `GET /api/v1/payments/checkout/` – Premium checkout page (Admin only)
* `POST /api/v1/payments/webhook/` – Razorpay webhook endpoint (no auth required)

### Admin Payments Monitoring
* `GET /api/v1/admin/payments/` – List all payments (Super Admin only)
* `GET /api/v1/admin/payments/<id>/` – Get payment details (Super Admin only)
* `GET /api/v1/admin/subscriptions/` – List all subscriptions (Super Admin only)
* `GET /api/v1/admin/subscriptions/<id>/` – Get subscription details (Super Admin only)
* `GET /api/v1/admin/webhooks/` – List webhook events (Super Admin only)
* `GET /api/v1/admin/webhooks/<id>/` – Get webhook event details (Super Admin only)

## Development

### Create Migrations
```bash
python manage.py makemigrations
```

### Response Caching
The system uses decorator-based caching for catalog endpoints:

```python
@drf_cache_response(prefix="genres:list", ttl=120)
def list(self, request, *args, **kwargs):
    return super().list(request, *args, **kwargs)

@drf_invalidate_cache(pattern="cache:genres*")
def perform_create(self, serializer):
    return super().perform_create(serializer)
```

Cache keys include query parameters for accurate filtering. TTL is 120 seconds by default.

### Logging
Logs are configured in `core/logging.py` and can be customized via environment variables:
- `LOG_LEVEL` – Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `LOG_FILE_ENABLED` – Enable/disable file logging
- `LOG_CONSOLE_ENABLED` – Enable/disable console logging

**Log file location:** `logs/gamerhouse.log`

### Tenant Context
Tenant context is automatically managed during authentication using Python's context variables:
1. User authenticates with JWT token
2. `TenantJWTAuthentication` validates token and sets tenant context
3. Tenant is stored in a `ContextVar` for async-safe access
4. Query managers automatically filter by current tenant
5. Context is automatically cleaned up after request completes

To manually access tenant context in views/tasks:
```python
from core.context import current_tenant

tenant = current_tenant.get()
```

### Correlation IDs
Correlation IDs are automatically generated for request tracing:

```python
from core.context import get_correlation_id, set_correlation_id

# Set at request start (middleware handles this automatically)
set_correlation_id(str(uuid.uuid4()))

# Access in views/services
correlation_id = get_correlation_id()
```

## Deployment Considerations

### Environment Variables
Ensure all production environment variables are set, especially:
* `SECRET_KEY` – Use a strong, unique key
* `DEBUG=False`
* `ALLOWED_HOSTS` – Set to your domain
* Database credentials
* Redis connection strings
* SMTP credentials
* Razorpay credentials

### Database Migrations
Always run migrations before deploying:
```bash
python manage.py migrate
```

### Celery Beat Scheduled Tasks
The following tasks run automatically:
- **polling-reconcile-task** – Runs every 15 minutes to reconcile pending payments with Razorpay

## Payment & Subscription Flow

### 1. Order Creation
1. Admin requests premium: `POST /api/v1/payments/create-order/`
2. **Validation**: Checks if Tenant is already `PREMIUM` (idempotent).
3. **Razorpay**: Creates an Order via Razorpay API.
4. **Local DB**: Creates `Payment` record with status `CREATED`.
5. Returns `order_id` and `payment_id` to client.

### 2. Payment Verification (Client-Side)
1. Client initiates payment using `order_id` (from Step 1) via Razorpay Checkout.
2. User completes payment; Razorpay SDK returns:
   - `razorpay_order_id` (same as Step 1)
   - `razorpay_payment_id` (generated by Razorpay)
   - `razorpay_signature` (cryptographic signature for verification)
3. Client submits these to `POST /api/v1/payments/verify/`
4. **Verification Logic**:
   - Signature verification using Razorpay utility.
   - Fetches payment status from Razorpay to ensure it is `captured`.
5. **State Transition**: Updates local `Payment` status to `VERIFIED`.
6. **Activation**: Triggers `activate_premium` service to upgrade Tenant.

### 3. Webhook Processing (Preferred)
**Why Webhooks?**
Webhooks are the **primary source of truth**. They verify payments independently of the client-side flow.
1. Razorpay sends event to `POST /api/v1/payments/webhook/` (Signed with Webhook Secret)
   - Events: `payment.captured`, `payment.failed`
2. **Async Processing**: `process_webhook_task` (Celery) handles the event.
3. **Recovery**: If the client verification Step 2 was missed, this webhook will mark the payment as `PAID` -> `VERIFIED` and trigger `activate_premium`.

### 4. Polling (Fallback Mechanism)
**Why Polling?**
Polling acts as a **safety net** if both client-side verification and webhooks fail (e.g., missed webhook event).
1. **Scheduled Task**: `polling_reconcile_task` runs periodically.
2. **Logic**: Checks `CREATED` payments that are older than 2 minutes.
3. **Recovery**: Fetches status from Razorpay using the `razorpay_order_id` (stored in Step 1). If Razorpay says `captured`, the local status is updated and subscription activated.

### 5. Lifetime Subscription Logic
**How it works**
The system is designed for a "pay once, use forever" model.
1. **Data Model**:
   - `Tenant` has a status field: `PREMIUM` or `FREE`.
   - `Subscription` model has a One-to-One relationship with `Tenant`.
2. **Enforcement**:
   - When a payment is successfully verified (via any method: API, Webhook, or Polling), `activate_premium` is called.
   - Sets `Tenant.status = PREMIUM`.
   - Creates/Updates `Subscription` with `status = ACTIVE`.
   - **No Expiry**: The `Subscription` never expires.


## Status

#### **Complete:**
* Multi-tenancy architecture
* Role-based access control (Super Admin, Admin, Gamer)
* Email verification and OTP authentication
* Password reset functionality
* JWT authentication with token blacklisting
* Catalog management (Games, Genres, Platforms)
* Response caching for catalog endpoints
* Search and filtering for catalog
* Tenant game management
* Personal game library with progress tracking
* Free tier game limits (5 games)
* Advanced filtering and pagination
* Celery background task processing
* Redis caching
* Razorpay payment gateway integration
* Premium subscriptions and billing
* Webhook handling for payment status updates
* Automatic payment reconciliation
* Structured JSON logging with correlation IDs
* Context-based tenant isolation (async-safe)
