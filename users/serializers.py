from rest_framework import serializers
from .models import CustomUser


class RegisterSerializer(serializers.ModelSerializer):
    """
    Used for POST /api/auth/register/
    password is write-only — never returned in any response.
    create_user() handles password hashing automatically.
    """
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'role']
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 8},
            'role': {'required': False},          # defaults to VIEWER if omitted
        }

    def create(self, validated_data):
        # create_user() salts + hashes the password before saving
        return CustomUser.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    """
    Used for GET /api/auth/me/
    Read-only snapshot of the authenticated user's profile.
    """
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'role']
        read_only_fields = ['id', 'username', 'email', 'role']


class AdminUserSerializer(serializers.ModelSerializer):
    """
    Used for Admin-only user management endpoints.
    Admin can update role, email, username, and active status.
    Password is never exposed or editable through this serializer.
    """
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'role', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined']
