from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Transaction
import datetime

User = get_user_model()

class TransactionTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', password='p', role='ADMIN')
        self.analyst = User.objects.create_user(username='analyst', password='p', role='ANALYST')
        self.viewer1 = User.objects.create_user(username='viewer1', password='p', role='VIEWER')
        self.viewer2 = User.objects.create_user(username='viewer2', password='p', role='VIEWER')
        
        # Create some transactions
        self.t1 = Transaction.objects.create(user=self.viewer1, amount=100, type='INCOME', category='Salary', date=datetime.date.today())
        self.t2 = Transaction.objects.create(user=self.viewer2, amount=50, type='EXPENSE', category='Food', date=datetime.date.today())
        
        self.url = '/api/finance/transactions/'

    def test_role_enforcement_mutations(self):
        # Viewer cannot POST
        self.client.force_authenticate(user=self.viewer1)
        data = {'amount': 200, 'type': 'INCOME', 'category': 'Bonus', 'date': '2026-01-01'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Analyst cannot PATCH
        self.client.force_authenticate(user=self.analyst)
        response = self.client.patch(f'{self.url}{self.t1.id}/', {'amount': 150})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Admin CAN POST
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_visibility_rules(self):
        # Viewer sees only own
        self.client.force_authenticate(user=self.viewer1)
        response = self.client.get(self.url)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.t1.id))
        
        # Analyst sees all
        self.client.force_authenticate(user=self.analyst)
        response = self.client.get(self.url)
        self.assertEqual(len(response.data['results']), 2)

    def test_soft_delete(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f'{self.url}{self.t1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Row still in DB
        self.t1.refresh_from_db()
        self.assertTrue(self.t1.is_deleted)
        
        # Not returned in normal queryset
        response = self.client.get(self.url)
        # Should only see t2 now, plus whatever the Admin themselves have (which is 0)
        self.assertEqual(len(response.data['results']), 1)

    def test_filtering_and_search(self):
        self.client.force_authenticate(user=self.analyst)
        
        # Filter by type
        response = self.client.get(f'{self.url}?type=INCOME')
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.t1.id))
        
        # Search by category
        response = self.client.get(f'{self.url}?search=Food')
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.t2.id))

    def test_analytics_view_access(self):
        analytics_url = '/api/finance/analytics/'
        # Viewer denied
        self.client.force_authenticate(user=self.viewer1)
        response = self.client.get(analytics_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Analyst allowed
        self.client.force_authenticate(user=self.analyst)
        response = self.client.get(analytics_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_analytics_data(self):
        analytics_url = '/api/finance/analytics/'
        self.client.force_authenticate(user=self.admin)
        # t1=100 INCOME, t2=50 EXPENSE
        response = self.client.get(analytics_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['totals']['net_balance'], 50)
        self.assertEqual(response.data['totals']['total_income'], 100)
        self.assertEqual(response.data['totals']['total_expense'], 50)

