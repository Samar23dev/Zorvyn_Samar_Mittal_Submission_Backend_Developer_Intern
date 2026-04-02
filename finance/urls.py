from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import TransactionViewSet, AnalyticsView

router = DefaultRouter()
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('analytics/', AnalyticsView.as_view(), name='analytics'),
] + router.urls
