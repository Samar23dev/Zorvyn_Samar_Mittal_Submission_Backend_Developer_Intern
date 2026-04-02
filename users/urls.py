from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import RegisterView, MeView, UserManagementViewSet

# Admin user-management routes (auto-generates GET/PATCH/DELETE on /users/ and /users/<id>/)
router = DefaultRouter()
router.register(r'users', UserManagementViewSet, basename='user-management')

urlpatterns = [
    # Registration — open to all
    path('register/', RegisterView.as_view(), name='register'),

    # Profile — requires Bearer token
    path('me/', MeView.as_view(), name='me'),

    # JWT login — returns access + refresh tokens
    path('login/', TokenObtainPairView.as_view(), name='login'),

    # JWT refresh — exchanges a refresh token for a new access token
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Admin-only user management (list, retrieve, update role/status, deactivate)
    path('', include(router.urls)),
]
