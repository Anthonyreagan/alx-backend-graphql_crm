# seed_db.py
import os
import django
from django.conf import settings

# This block is essential for standalone script execution
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx-backend-graphql_crm.settings')
    django.setup()

from crm.models import Customer, Product, Order
from decimal import Decimal

print("Seeding CRM database...")

# Clear existing data (optional, for fresh runs)
# Customer.objects.all().delete()
# Product.objects.all().delete()
# Order.objects.all().delete()

# --- Create Customers ---
customers_data = [
    {"name": "Alice Wonderland", "email": "alice@example.com", "phone": "+1234567890"},
    {"name": "Bob The Builder", "email": "bob@example.com", "phone": "123-456-7890"},
    {"name": "Charlie Chaplin", "email": "charlie@example.com"}, # No phone
    {"name": "Diana Prince", "email": "diana@example.com", "phone": "(987) 654-3210"},
]

for data in customers_data:
    try:
        customer, created = Customer.objects.get_or_create(email=data['email'], defaults=data)
        if created:
            print(f"Created customer: {customer.name}")
        else:
            print(f"Customer already exists: {customer.name}")
    except Exception as e:
        print(f"Error creating customer {data['name']}: {e}")

# --- Create Products ---
products_data = [
    {"name": "Laptop", "price": Decimal("1200.50"), "stock": 10},
    {"name": "Mouse", "price": Decimal("25.00"), "stock": 50},
    {"name": "Keyboard", "price": Decimal("75.99"), "stock": 30},
    {"name": "Monitor", "price": Decimal("300.00"), "stock": 5},
]

for data in products_data:
    try:
        product, created = Product.objects.get_or_create(name=data['name'], defaults=data)
        if created:
            print(f"Created product: {product.name}")
        else:
            print(f"Product already exists: {product.name}")
    except Exception as e:
        print(f"Error creating product {data['name']}: {e}")

print("\nDatabase seeding complete.")
print("You can now test GraphQL queries and mutations.")
