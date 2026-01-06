# Store Locator Service

This is a backend project for managing and searching retail store locations. It features geocoding, distance-based searches, and comprehensive role-based access control.

## Frameworks & Technologies
- **Core Framework:** FastAPI (Python)
- **Database:** PostgreSQL with SQLAlchemy ORM
- **Cache & Rate Limiting:** Redis
- **Migrations:** Alembic
- **Security:** PyJWT for authentication and Bcrypt for password hashing
- **Geospatial:** Geopy for coordinate and distance calculations
- **Testing:** Pytest and Httpx

## API Endpoints
<img width="1418" height="772" alt="image" src="https://github.com/user-attachments/assets/af94236d-cfb1-4cbc-b6aa-0df8fe874b0a" />

<img width="1395" height="745" alt="image" src="https://github.com/user-attachments/assets/826fb2a6-74c6-4107-8652-2e9ab97408e6" />

### Health Check
- `GET /`: Basic service health status.

### Store Search (Public)
- `POST /api/stores/search`: Find stores by coordinates, address, or postal code with filtering.

### Authentication
- `POST /api/auth/login`: Authenticate and receive access/refresh tokens.
- `POST /api/auth/refresh`: Obtain a new access token using a refresh token.
- `POST /api/auth/logout`: Securely log out and revoke active tokens.

### Store Management (Admin/Marketer)
- `GET /api/admin/stores`: Retrieve a paginated list of all stores.
- `POST /api/admin/stores`: Manually create a new store location.
- `GET /api/admin/stores/{id}`: Fetch detailed information for a specific store.
- `PATCH /api/admin/stores/{id}`: Update existing store details.
- `DELETE /api/admin/stores/{id}`: Soft-delete (deactivate) a store.
- `POST /api/admin/stores/import`: Batch import store data using a CSV file.

### User Management (Admin Only)
- `GET /api/admin/users`: List all registered users.
- `POST /api/admin/users`: Register a new administrative or marketer user.
- `PUT /api/admin/users/{id}`: Update user roles or account status.
- `DELETE /api/admin/users/{id}`: Deactivate a user account.

## Project Initiation

1. **Environment Setup**: Ensure Docker is installed and create a `.env` file with necessary credentials.
2. **Launch Service**: Execute `docker-compose up --build` to start the API, PostgreSQL, and Redis containers.
3. **Automatic Setup**: The application automatically handles database migrations and initializes a default admin account on startup.
4. **Interactive Docs**: Access the full Swagger documentation at `http://localhost:8000/docs` once the service is active.
5. **Local Development**: Alternatively, install dependencies via `pip install -r requirements.txt` and run `uvicorn main:app --reload`.

