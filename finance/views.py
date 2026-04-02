from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Q
from users.permissions import IsAdmin, IsAnalystOrAdmin
from .models import Transaction
from .serializers import TransactionSerializer
class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class   = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields   = ['type', 'category', 'date']
    search_fields      = ['category', 'notes']
    ordering_fields    = ['date', 'amount']

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

class AnalyticsView(APIView):
    permission_classes = [IsAnalystOrAdmin]

    def get(self, request):
        qs = Transaction.objects.filter(is_deleted=False)
        if request.user.role not in ('ADMIN', 'ANALYST'):
            qs = qs.filter(user=request.user)

        totals = qs.aggregate(
            total_income  = Sum('amount', filter=Q(type='INCOME')),
            total_expense = Sum('amount', filter=Q(type='EXPENSE')),
        )
        totals['net_balance'] = (totals['total_income'] or 0) - (totals['total_expense'] or 0)
        by_category = list(qs.values('category').annotate(total=Sum('amount'), count=Count('id')))
        return Response({'totals': totals, 'by_category': by_category})
