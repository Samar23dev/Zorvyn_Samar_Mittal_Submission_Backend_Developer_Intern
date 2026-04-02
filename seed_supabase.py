import os
import django
from decimal import Decimal
from datetime import date

# 1. Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from finance.models import Transaction

User = get_user_model()

def seed():
    print("--- Starting Supabase Indian-Style Data Seeding ---")

    # 2. Define our Demo Users
    users_to_create = [
        {'username': 'adminsamar',   'email': 'samar@zorvyn.com',  'role': 'ADMIN',   'pw': 'Admin@12345'},
        {'username': 'analyst_priya', 'email': 'priya@zorvyn.com',  'role': 'ANALYST', 'pw': 'AnalystPassword123!'},
        {'username': 'viewer_rahul',  'email': 'rahul@zorvyn.com',  'role': 'VIEWER',  'pw': 'ViewerPassword123!'},
        {'username': 'viewer_amit',   'email': 'amit@zorvyn.com',   'role': 'VIEWER',  'pw': 'ViewerPassword123!'},
    ]

    user_objects = {}
    for u in users_to_create:
        user, created = User.objects.get_or_create(
            username=u['username'],
            defaults={'email': u['email'], 'role': u['role']}
        )
        if created:
            user.set_password(u['pw'])
            print(f"Created {u['role']}: {u['username']}")
        else:
            user.role = u['role'] # Ensure role is correct
            print(f"User exists: {u['username']}")
        user.save()
        user_objects[u['username']] = user

    # 3. Define Transaction Data (Indian Currency Style)
    # We use 10,000s and 100,000s to feel like INR (though stored as standard Decimals)
    transactions = [
        # --- Admin Samar (Organization Head) Data ---
        {'user': user_objects['adminsamar'], 'amount': 150000.00, 'type': 'INCOME',  'category': 'Salary',     'date': date(2026, 3, 31), 'notes': 'Monthly Salary'},
        {'user': user_objects['adminsamar'], 'amount': 45000.00,  'type': 'EXPENSE', 'category': 'Rent',       'date': date(2026, 3, 1),  'notes': 'BHK Rent in Bangalore'},
        {'user': user_objects['adminsamar'], 'amount': 12500.00,  'type': 'EXPENSE', 'category': 'Investment', 'date': date(2026, 3, 10), 'notes': 'SIP Mutual Fund'},
        {'user': user_objects['adminsamar'], 'amount': 4200.00,   'type': 'EXPENSE', 'category': 'Leisure',    'date': date(2026, 3, 15), 'notes': 'Weekend Shopping'},
        
        # --- Analyst Priya (Seeing Global Data) ---
        {'user': user_objects['analyst_priya'], 'amount': 95000.00, 'type': 'INCOME',  'category': 'Salary',    'date': date(2026, 3, 31), 'notes': 'Monthly Salary'},
        {'user': user_objects['analyst_priya'], 'amount': 2500.00,  'type': 'EXPENSE', 'category': 'Dining',    'date': date(2026, 3, 5),  'notes': 'Zomato/Swiggy Order'},
        {'user': user_objects['analyst_priya'], 'amount': 1200.00,  'type': 'EXPENSE', 'category': 'Internet',  'date': date(2026, 3, 12), 'notes': 'Airtel Broadband'},
        
        # --- Viewer Rahul (Personal Data only) ---
        {'user': user_objects['viewer_rahul'], 'amount': 60000.00, 'type': 'INCOME',  'category': 'Salary',    'date': date(2026, 3, 31), 'notes': 'Contract Pay'},
        {'user': user_objects['viewer_rahul'], 'amount': 15000.00, 'type': 'EXPENSE', 'category': 'Education', 'date': date(2026, 3, 20), 'notes': 'Upskilling Course'},
        {'user': user_objects['viewer_rahul'], 'amount': 3000.00,  'type': 'EXPENSE', 'category': 'Travel',    'date': date(2026, 3, 15), 'notes': 'Ola/Uber Cabs'},
        
        # --- Viewer Amit (Personal Data only) ---
        {'user': user_objects['viewer_amit'], 'amount': 45000.00, 'type': 'INCOME',  'category': 'Salary',    'date': date(2026, 3, 31), 'notes': 'Internship Stipend'},
        {'user': user_objects['viewer_amit'], 'amount': 1000.00,  'type': 'EXPENSE', 'category': 'Leisure',   'date': date(2026, 3, 25), 'notes': 'Movie Night'},
    ]

    for data in transactions:
        Transaction.objects.get_or_create(
            user=data['user'],
            amount=data['amount'],
            type=data['type'],
            category=data['category'],
            date=data['date'],
            defaults={'notes': data['notes']}
        )
    
    print(f"--- Seeding Successfully Completed: Unified data for {len(user_objects)} users ---")

if __name__ == "__main__":
    seed()
