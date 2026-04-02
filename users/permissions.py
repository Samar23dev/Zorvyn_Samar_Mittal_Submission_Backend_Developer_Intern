from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """
    Grants access only to users with role = 'ADMIN'.
    Used on:
      - All transaction mutations (create, update, partial_update, destroy)
      - All user management endpoints (GET/PATCH/DELETE /api/auth/users/)
    """
    message = "Only Admin users can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'ADMIN'
        )


class IsAnalystOrAdmin(BasePermission):
    """
    Grants access to users with role = 'ANALYST' or 'ADMIN'.
    Used on: GET /api/finance/analytics/  (Phase 4 — Analyst and Admin can see summaries)
    Viewers are excluded from the analytics endpoint.
    """
    message = "Only Analyst or Admin users can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('ANALYST', 'ADMIN')
        )
