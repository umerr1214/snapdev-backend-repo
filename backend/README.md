# SnapDev Portal - Backend API (Admin Only)

A FastAPI-based backend server for the SnapDev Portal application with MongoDB Atlas integration. This is an admin-only system for managing projects.

## Features

- 🚀 **FastAPI** - Modern, fast web framework for building APIs
- 🍃 **MongoDB Atlas** - Cloud-based NoSQL database
- 🔐 **JWT Authentication** - Secure admin authentication
- 📁 **Project Management** - CRUD operations for projects
- 🔒 **Admin-only Access** - Restricted to admin users only
- 📚 **Auto-generated Documentation** - Interactive API docs with Swagger UI
- 🌐 **CORS Support** - Cross-origin resource sharing for frontend integration

## Project Structure

```
backend/
├── routes/
│   ├── __init__.py
│   ├── auth.py          # Admin authentication endpoints
│   └── projects.py      # Project management endpoints
├── .env                 # Environment variables
├── database.py          # MongoDB connection and configuration
├── main.py             # FastAPI application entry point
├── start.py            # Startup script
├── create_admin.py     # Admin user creation script
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip3 install -r requirements.txt
```

### 2. Environment Setup

The `.env` file is already configured with your MongoDB Atlas connection. Update the `SECRET_KEY` for production:

```env
MONGODB_URL=mongodb+srv://backend:backend123#@cluster0.fy9abew.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
DATABASE_NAME=snapdev_portal
SECRET_KEY=your-secret-key-here-change-in-production
```

### 3. Create Admin User

An admin user has already been created with these credentials:

- **Email**: admin@gmail.com
- **Password**: admin123#

If you need to create a new admin user, run:

```bash
python3 create_admin.py
```

### 4. Start the Server

```bash
# Option 1: Using the startup script
python3 start.py

# Option 2: Using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Option 3: Using the main.py file
python3 main.py
```

The server will start at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:

- **Interactive API Docs (Swagger UI)**: http://localhost:8000/docs
- **Alternative API Docs (ReDoc)**: http://localhost:8000/redoc
- **OpenAPI JSON Schema**: http://localhost:8000/openapi.json

## API Endpoints

### Health Check

- `GET /` - Root endpoint with API information
- `GET /health` - Health check endpoint with database status

### Admin Authentication (`/api/auth`)

- `POST /api/auth/login` - Login admin (returns JWT token)
- `GET /api/auth/me` - Get current admin information
- `POST /api/auth/logout` - Logout admin

### Projects (`/api/projects`)

- `POST /api/projects/` - Create a new project
- `GET /api/projects/` - Get all projects
- `GET /api/projects/{project_id}` - Get project by ID
- `PUT /api/projects/{project_id}` - Update project
- `DELETE /api/projects/{project_id}` - Delete project
- `GET /api/projects/status/{status}` - Get projects by status

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. To access protected endpoints:

1. Login with admin credentials at `/api/auth/login`
2. Use the returned `access_token` in the Authorization header:
   ```
   Authorization: Bearer <your_access_token>
   ```

### Admin Credentials

- **Email**: admin@gmail.com
- **Password**: admin123#

## Database Collections

The application uses the following MongoDB collections:

- **users**: Admin user accounts and authentication data
- **projects**: Project information and metadata

## Development

### Running in Development Mode

The server runs in development mode by default with auto-reload enabled. Any changes to the code will automatically restart the server.

### Environment Variables

| Variable                      | Description                     | Default          |
| ----------------------------- | ------------------------------- | ---------------- |
| `MONGODB_URL`                 | MongoDB Atlas connection string | Required         |
| `DATABASE_NAME`               | Database name                   | `snapdev_portal` |
| `SECRET_KEY`                  | JWT secret key                  | Required         |
| `ALGORITHM`                   | JWT algorithm                   | `HS256`          |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time           | `30`             |
| `HOST`                        | Server host                     | `0.0.0.0`        |
| `PORT`                        | Server port                     | `8000`           |
| `DEBUG`                       | Debug mode                      | `True`           |

## Testing the API

You can test the API using the interactive documentation at `/docs` or with curl:

### Login

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@gmail.com&password=admin123#"
```

### Create Project

```bash
curl -X POST "http://localhost:8000/api/projects/" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Project",
    "description": "A test project",
    "technology_stack": ["Python", "FastAPI"],
    "status": "active"
  }'
```

## Production Deployment

For production deployment:

1. Set `DEBUG=False` in the `.env` file
2. Use a strong, unique `SECRET_KEY`
3. Configure proper CORS origins in `main.py`
4. Use a production WSGI server like Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

## Error Handling

The API includes comprehensive error handling with appropriate HTTP status codes:

- `400` - Bad Request (invalid data)
- `401` - Unauthorized (authentication required)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (resource doesn't exist)
- `422` - Unprocessable Entity (validation errors)
- `500` - Internal Server Error

## Security Features

- Password hashing using bcrypt
- JWT token-based authentication
- Admin-only access control
- Input validation with Pydantic
- CORS protection
- Environment variable configuration

## Support

For issues and questions, please refer to the project documentation or create an issue in the project repository.
