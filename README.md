# Zorvyn Finance Dashboard — Backend API

An enterprise-grade, Role-Based Finance Dashboard API built to securely manage user transactions, analytics, and permissions across different tiered roles.

---

## 🛠️ Tech Stack
- **Framework:** Django 6.0.3 + Django REST Framework 3.17
- **Authentication:** JWT (JSON Web Tokens) via `djangorestframework-simplejwt`
- **Database:** PostgreSQL (Supabase Cloud compatible)
- **Deployment:** AWS Elastic Beanstalk
- **API Documentation:** Swagger / OpenAPI via `drf-spectacular`

---

## ✨ Key Features
- **Strict Role-Based Access Control (RBAC):** Built-in 3-tier user hierarchy (`VIEWER`, `ANALYST`, `ADMIN`) governed by custom DRF Permission classes.
- **Data Isolation:** Normal users can only fetch and interact with their own isolated data, while Analysts/Admins have aggregated visibility across the application.
- **Soft Deletion Architecture:** Deleting users and transactions safely flags rows with `is_active=False` or `is_deleted=True` to preserve referential database integrity and historical calculation accuracy.
- **Global Analytical Aggregation:** Real-time summary endpoints computing total income, expected expenses, and net balances via automated ORM queries.

---

## 🔒 Role-Based Access Matrix

| Endpoint | 👁️ Viewer | 📊 Analyst | 🔑 Admin |
|---|---|---|---|
| `GET /api/finance/transactions/` | ✅ Own only | ✅ **All users'** | ✅ All users' |
| `POST /api/finance/transactions/` | ❌ | ❌ | ✅ |
| `GET /api/finance/transactions/<id>/` | ✅ Own only | ✅ Any | ✅ Any |
| `PATCH /api/finance/transactions/<id>/` | ❌ | ❌ | ✅ |
| `DELETE /api/finance/transactions/<id>/` | ❌ | ❌ | ✅ (soft) |
| `GET /api/finance/analytics/` | ❌ | ✅ | ✅ |

*(User management endpoints `/api/auth/users/` are strictly locked entirely to `ADMIN` users).*

---

## 🏁 How to Run Locally

### 1. Environment Setup
Create a `.env` file in the root `backend/` directory:

```env
SECRET_KEY=your-super-secret-key
DEBUG=True
ALLOWED_HOSTS=*

# Database
DB_ENGINE=django.db.backends.sqlite3
# DB_HOST=aws-1-ap-southeast-2.pooler.supabase.com
```

### 2. Installation & Server Initialization
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install Dependencies
pip install -r requirements.txt

# Apply Database Migrations
python manage.py migrate

# Create a Superuser (Admin) to log in
python manage.py createsuperuser

# Start the Development Server
python manage.py runserver
```

---

## 🧪 Running Automated Tests
The application is secured by 12 comprehensive DRF `APITestCase` modules checking for correct Role constraint enforcement and data routing.

Make sure your `.env` is pointing to a local database (like SQLite) to allow Django to automatically generate its dummy `test_db` safely, then run:

```bash
python manage.py test
```

---

## 📖 API Documentation Reference
Once the server is running, the live API documentation is automatically accessible via Swagger UI.

Full Interactive Documentation: `http://127.0.0.1:8000/api/docs/`

| Method | URL | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register/` | None | Register new user (defaults to VIEWER) |
| POST | `/api/auth/login/` | None | Get JWT access + refresh tokens |
| POST | `/api/auth/token/refresh/` | None | Refresh access token |
| GET | `/api/auth/me/` | Bearer | Current user's own profile |
| GET | `/api/auth/users/` | Bearer + Admin | List all users |
| PATCH | `/api/auth/users/<id>/` | Bearer + Admin | Update role / email / active status |
| DELETE | `/api/auth/users/<id>/` | Bearer + Admin | Soft-deactivate user |
| GET | `/api/finance/transactions/` | Bearer | List transactions |
| POST | `/api/finance/transactions/` | Bearer + Admin | Create transaction |
| GET | `/api/finance/analytics/` | Bearer + Analyst/Admin | Aggregated totals by category |

---

## 🚀 Deployment
This application requires **Gunicorn** and **Whitenoise** for production deployment. It is configured for AWS Elastic Beanstalk and includes an `.ebextensions/django.config` file to natively map the WSGI path for Amazon Linux environments. 

Make sure to map the internal Database `.env` properties inside the AWS console during deployment configuration.
