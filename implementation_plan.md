# Finance Dashboard Backend — Implementation Plan

## Overview
Building the Role-Based Finance Dashboard API using **maximum prebuilt tooling** from Django,
Django REST Framework, and `djangorestframework-simplejwt`.

**Stack:** Django 6.0.3 · DRF 3.17 · SimpleJWT · drf-spectacular · PostgreSQL · python-decouple

---

## Prebuilt-First Strategy

| Need | Prebuilt Tool | Custom Code |
|---|---|---|
| JWT Login / Refresh | `TokenObtainPairView` / `TokenRefreshView` | None |
| Registration endpoint | `generics.CreateAPIView` | Serializer only |
| Full CRUD (transactions) | `ModelViewSet` | `get_queryset` + `perform_*` + `get_permissions` overrides |
| Full CRUD (user mgmt) | `ModelViewSet` | `perform_destroy` soft-deactivate override |
| URL routing | `DefaultRouter` | None |
| Serialization + validation | `ModelSerializer` | Field config only |
| Pagination | `PageNumberPagination` (global in settings) | None |
| Filtering / search / ordering | `DjangoFilterBackend` + `SearchFilter` + `OrderingFilter` | None |
| API Docs | `SpectacularSwaggerView` | None |
| Password hashing | `create_user()` built-in | None |
| Aggregation analytics | ORM `Sum`, `Count`, `.values().annotate()` | View logic only |

---

## ✅ Phase 0 — Project Scaffold
**Status: COMPLETE**

- [x] Django project (`config/`) created
- [x] `users` app — `CustomUser` model (UUID PK, role field, extends `AbstractUser`)
- [x] `finance` app — `Transaction` model (UUID PK, ForeignKey, soft-delete)
- [x] DRF, SimpleJWT, drf-spectacular installed

---

## ✅ Phase 1 — Environment Setup
**Status: COMPLETE**

- [x] Installed: `django-filter`, `django-cors-headers`, `python-decouple`, `psycopg2-binary`
- [x] Created `backend/.env` — all secrets externalized
- [x] Rewrote `config/settings.py` — JWT, CORS, pagination, filter backends, Supabase SSL
- [x] Scaffolded missing `finance` app files (`__init__.py`, `apps.py`, `migrations/__init__.py`)
- [x] Created `requirements.txt`
- [x] Created PostgreSQL DB: `zorvyn`
- [x] Applied all 21 migrations — ✅ OK
- [x] Created superuser: `adminsamar`

---

## ✅ Phase 2 — Users App: Auth & Permissions
**Status: COMPLETE** — verified `2026-04-02`

### Files

#### `users/models.py`
`CustomUser` — UUID PK, 3-tier RBAC, extends `AbstractUser`:
```python
class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        VIEWER  = 'VIEWER',  'Viewer'
        ANALYST = 'ANALYST', 'Analyst'
        ADMIN   = 'ADMIN',   'Admin'

    id   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.VIEWER)
```

#### `users/serializers.py`
Three serializers — each scoped to its exact use case:

| Serializer | Used by | Writable fields |
|---|---|---|
| `RegisterSerializer` | `POST /api/auth/register/` | username, email, password (write-only, min 8), role (optional) |
| `UserSerializer` | `GET /api/auth/me/` | None — fully read-only |
| `AdminUserSerializer` | `GET/PATCH /api/auth/users/` | username, email, role, is_active |

Password is **never** readable or writable through `AdminUserSerializer`.

#### `users/permissions.py`
Two permission classes extending `BasePermission`:

| Class | Allows | Used on |
|---|---|---|
| `IsAdmin` | `role == 'ADMIN'` only | All transaction mutations + all user management endpoints |
| `IsAnalystOrAdmin` | `role in ('ANALYST', 'ADMIN')` | `GET /api/finance/analytics/` (Phase 4) |

Both reject unauthenticated requests before role checks run.

#### `users/views.py`
Three views:

- `RegisterView` — `generics.CreateAPIView`, `AllowAny`
- `MeView` — `generics.RetrieveAPIView`, `IsAuthenticated`, overrides `get_object()` to return `request.user`
- `UserManagementViewSet` — `ModelViewSet`, `IsAdmin` on all actions, POST disabled (registration is the only creation path), `perform_destroy` soft-deactivates (`is_active=False`) instead of hard-deleting

#### `users/urls.py`
Router + manual paths combined:
```python
router.register(r'users', UserManagementViewSet, basename='user-management')
# Auto-creates: GET/PATCH/DELETE /api/auth/users/ and /api/auth/users/<id>/
```
Plus manual: `register/`, `me/`, `login/`, `token/refresh/`

### Verification Results
| Check | Result |
|---|---| 
| `python -m py_compile` on all users files | ✅ No syntax errors |
| `manage.py check` | ✅ **0 issues** |

---

## ✅ Phase 3 — Finance App: Transactions CRUD
**Status: COMPLETE** — verified `2026-04-02`

### `finance/models.py`
```python
class Transaction(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount     = models.DecimalField(max_digits=12, decimal_places=2)
    type       = models.CharField(max_length=10, choices=TransactionType.choices)
    category   = models.CharField(max_length=50)
    date       = models.DateField()
    notes      = models.TextField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
```

### `finance/serializers.py`
`ModelSerializer` — auto-maps all fields, auto-validates types:
```python
class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Transaction
        fields = ['id', 'amount', 'type', 'category', 'date', 'notes']
        read_only_fields = ['id']
```

### `finance/views.py`
`ModelViewSet` with role-aware queryset and strict permission gating:
```python
class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends  = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['type', 'category', 'date']
    search_fields    = ['category', 'notes']
    ordering_fields  = ['date', 'amount']

    def get_queryset(self):
        qs = Transaction.objects.filter(is_deleted=False)
        # Admin and Analyst see ALL transactions; Viewer sees only their own
        if self.request.user.role in ('ADMIN', 'ANALYST'):
            return qs
        return qs.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        instance.is_deleted = True   # soft-delete, not SQL DELETE
        instance.save()

    def get_permissions(self):
        # Only Admin can create, edit, or delete
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        # Analyst and Viewer can read (queryset scoping enforces what they see)
        return [IsAuthenticated()]
```

### `finance/urls.py`
`DefaultRouter` auto-generates all 5 CRUD routes — no manual `path()` calls:
```python
router = DefaultRouter()
router.register(r'transactions', TransactionViewSet, basename='transaction')
urlpatterns = router.urls
```

### `finance/admin.py`
```python
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'category', 'amount', 'date', 'is_deleted']
    list_filter  = ['type', 'is_deleted']
```

### Verification Results
| Check | Result |
|---|---|
| `python -m py_compile finance/*.py` | ✅ No syntax errors |
| `manage.py check` | ✅ **0 issues** |

---

## ✅ Phase 4 — Analytics Endpoint
**Status: COMPLETE**

Add `AnalyticsView` to `finance/views.py` using ORM aggregation — no raw SQL.
Permission: `IsAnalystOrAdmin` (Viewer is excluded from summaries).

```python
class AnalyticsView(APIView):
    permission_classes = [IsAnalystOrAdmin]

    def get(self, request):
        qs = Transaction.objects.filter(user=request.user, is_deleted=False)
        totals = qs.aggregate(
            total_income  = Sum('amount', filter=Q(type='INCOME')),
            total_expense = Sum('amount', filter=Q(type='EXPENSE')),
        )
        totals['net_balance'] = (totals['total_income'] or 0) - (totals['total_expense'] or 0)
        by_category = list(qs.values('category').annotate(total=Sum('amount'), count=Count('id')))
        return Response({'totals': totals, 'by_category': by_category})
```

> **Note for Admin:** `get_queryset` should return all transactions when `request.user.role == 'ADMIN'` (not scoped to self).

---

## ✅ Phase 5 — Wire All URLs + Swagger
**Status: COMPLETE**

### `config/urls.py` — [MODIFY]
Currently only has `admin/`. Needs to include all app URLs and Swagger:
```python
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/',       admin.site.urls),
    path('api/auth/',    include('users.urls')),
    path('api/finance/', include('finance.urls')),
    path('api/schema/',  SpectacularAPIView.as_view(),                      name='schema'),
    path('api/docs/',    SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
```

> ⚠️ Until this phase is done, **no API endpoints are reachable** (only Django Admin at `/admin/`).

---

## ✅ Phase 6 — Automated Tests
**Status: COMPLETE**

Run: `python manage.py test`

Tests to write using DRF's `APITestCase`:
- Register user, login, get tokens
- Role enforcement on transactions: Viewer/Analyst cannot POST/PATCH/DELETE
- Analyst sees all transactions, Viewer sees only their own
- Soft-delete: `DELETE` sets `is_deleted=True`, row still in DB
- User management: non-Admin cannot access `/api/auth/users/`
- User deactivation: `DELETE /api/auth/users/<id>/` sets `is_active=False`, row preserved

---

## Role-Based Access Matrix

### Transaction Endpoints

| Endpoint | 👁️ Viewer | 📊 Analyst | 🔑 Admin |
|---|---|---|---|
| `GET /api/finance/transactions/` | ✅ Own only | ✅ **All users'** | ✅ All users' |
| `POST /api/finance/transactions/` | ❌ | ❌ | ✅ |
| `GET /api/finance/transactions/<id>/` | ✅ Own only | ✅ Any | ✅ Any |
| `PATCH /api/finance/transactions/<id>/` | ❌ | ❌ | ✅ |
| `DELETE /api/finance/transactions/<id>/` | ❌ | ❌ | ✅ (soft) |
| `GET /api/finance/analytics/` | ❌ | ✅ | ✅ |

### Auth & User Management Endpoints

| Endpoint | 👁️ Viewer | 📊 Analyst | 🔑 Admin |
|---|---|---|---|
| `POST /api/auth/register/` | ✅ | ✅ | ✅ |
| `POST /api/auth/login/` | ✅ | ✅ | ✅ |
| `POST /api/auth/token/refresh/` | ✅ | ✅ | ✅ |
| `GET /api/auth/me/` | ✅ | ✅ | ✅ |
| `GET /api/auth/users/` | ❌ | ❌ | ✅ |
| `GET /api/auth/users/<id>/` | ❌ | ❌ | ✅ |
| `PATCH /api/auth/users/<id>/` | ❌ | ❌ | ✅ |
| `DELETE /api/auth/users/<id>/` | ❌ | ❌ | ✅ (soft-deactivate) |

---

## Complete API Reference

| Method | URL | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register/` | None | Register new user (defaults to VIEWER) |
| POST | `/api/auth/login/` | None | Get JWT access + refresh tokens |
| POST | `/api/auth/token/refresh/` | None | Refresh access token |
| GET | `/api/auth/me/` | Bearer | Current user's own profile |
| GET | `/api/auth/users/` | Bearer + Admin | List all users |
| GET | `/api/auth/users/<id>/` | Bearer + Admin | Retrieve any user |
| PATCH | `/api/auth/users/<id>/` | Bearer + Admin | Update role / email / username / active status |
| DELETE | `/api/auth/users/<id>/` | Bearer + Admin | Soft-deactivate user (is_active=False) |
| GET | `/api/finance/transactions/` | Bearer | List transactions (role-scoped) |
| POST | `/api/finance/transactions/` | Bearer + Admin | Create transaction |
| GET | `/api/finance/transactions/<id>/` | Bearer | Get single transaction |
| PATCH | `/api/finance/transactions/<id>/` | Bearer + Admin | Update transaction |
| DELETE | `/api/finance/transactions/<id>/` | Bearer + Admin | Soft-delete transaction |
| GET | `/api/finance/analytics/` | Bearer + Analyst/Admin | Aggregated totals by category |
| GET | `/api/docs/` | None | Swagger UI |
| GET | `/api/schema/` | None | OpenAPI schema (JSON) |
