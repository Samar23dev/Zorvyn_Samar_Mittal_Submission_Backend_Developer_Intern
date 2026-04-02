from rest_framework import generics, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import CustomUser
from .serializers import RegisterSerializer, UserSerializer, AdminUserSerializer
from users.permissions import IsAdmin


class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/
    Open to everyone — no auth required.
    DRF's CreateAPIView handles: deserialize → validate → create → 201 response.
    """
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class MeView(generics.RetrieveAPIView):
    """
    GET /api/auth/me/
    Returns the profile of the currently authenticated user.
    get_object() is overridden to always return request.user (no pk in URL).
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserManagementViewSet(viewsets.ModelViewSet):
    """
    Admin-only: full user management.
    GET    /api/auth/users/         — list all users
    GET    /api/auth/users/<id>/    — retrieve any user
    PATCH  /api/auth/users/<id>/    — update role, email, username, is_active
    DELETE /api/auth/users/<id>/    — deactivate user (soft, sets is_active=False)

    Password is never exposed or writable through this surface.
    """
    queryset = CustomUser.objects.all().order_by('date_joined')
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdmin]
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']  # no POST (use /register/)

    def perform_destroy(self, instance):
        # Soft-deactivate instead of hard-delete — preserves transaction history
        instance.is_active = False
        instance.save()

