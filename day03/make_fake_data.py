"""
Day 3 - #30DaysOfAutomation (Pharmacy Edition)
Creates FAKE pharmacy data for practice:
    data/products.csv          -> product catalog with stock
    data/sales_counter.csv     -> sales at the counter
    data/orders_online.csv     -> WhatsApp / online orders
    data/orders_delivery.csv   -> delivery orders

Each sales file has DIFFERENT column names on purpose,
because in real life every source exports data differently.

Usage:
    python make_fake_data.py
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(7)  # same fake data every time you run it

data_dir = Path(__file__).parent / "data"
data_dir.mkdir(exist_ok=True)

# name, category, price (ILS), stock, minimum stock
PRODUCTS = [
    ("Panadol 500mg 24 tabs", "OTC", 18, 40, 15),
    ("Panadol Extra 24 tabs", "OTC", 22, 8, 15),
    ("Brufen 400mg 30 tabs", "OTC", 20, 25, 10),
    ("Strepsils Honey Lemon", "OTC", 24, 30, 10),
    ("Otrivin Nasal Spray", "OTC", 21, 6, 10),
    ("Gaviscon Liquid 200ml", "OTC", 32, 12, 8),
    ("Augmentin 1g 14 tabs", "Prescription", 55, 18, 10),
    ("Glucophage 850mg 30 tabs", "Prescription", 25, 35, 20),
    ("Concor 5mg 30 tabs", "Prescription", 38, 9, 12),
    ("Lipitor 20mg 30 tabs", "Prescription", 90, 14, 8),
    ("Nexium 40mg 14 tabs", "Prescription", 60, 5, 8),
    ("Vitamin D3 1000IU 60 caps", "Vitamins", 45, 22, 10),
    ("Omega 3 Fish Oil 60 caps", "Vitamins", 70, 16, 8),
    ("Centrum Adults 30 tabs", "Vitamins", 85, 7, 8),
    ("Vitamin C 1000mg Effervescent", "Vitamins", 30, 28, 10),
    ("Iron + Folic Acid 30 tabs", "Vitamins", 35, 11, 8),
    ("La Roche-Posay Sunscreen SPF50", "Cosmetics", 120, 9, 5),
    ("CeraVe Moisturizing Cream", "Cosmetics", 95, 4, 5),
    ("Bioderma Micellar Water", "Cosmetics", 75, 13, 6),
    ("Vaseline Lip Therapy", "Cosmetics", 15, 50, 15),
    ("Bebelac 1 Milk 400g", "Baby Care", 65, 20, 10),
    ("Pampers Size 4 (44)", "Baby Care", 70, 6, 10),
    ("Johnson's Baby Shampoo 300ml", "Baby Care", 28, 18, 8),
    ("Sudocrem 125g", "Baby Care", 40, 10, 6),
]

# Products that sell more often (to make the report interesting)
POPULAR = ["Panadol 500mg 24 tabs", "Vitamin D3 1000IU 60 caps", "Glucophage 850mg 30 tabs",
           "Pampers Size 4 (44)", "Strepsils Honey Lemon", "Vitamin C 1000mg Effervescent"]

price_of = {name: price for name, _, price, _, _ in PRODUCTS}
names = [p[0] for p in PRODUCTS]
weights = [4 if n in POPULAR else 1 for n in names]

start = date(2026, 11, 1)  # one week of sales
week = [start + timedelta(days=i) for i in range(7)]

# 1) Product catalog
with open(data_dir / "products.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["product", "category", "price", "stock", "min_stock"])
    w.writerows(PRODUCTS)

# 2) Counter sales: date, product, qty, unit_price
with open(data_dir / "sales_counter.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["date", "product", "qty", "unit_price"])
    for day in week:
        for _ in range(random.randint(25, 40)):
            p = random.choices(names, weights)[0]
            w.writerow([day.isoformat(), p, random.randint(1, 3), price_of[p]])

# 3) Online / WhatsApp orders: different column names + date format
with open(data_dir / "orders_online.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["order_date", "item_name", "quantity", "price"])
    for day in week:
        for _ in range(random.randint(5, 12)):
            p = random.choices(names, weights)[0]
            w.writerow([day.strftime("%d/%m/%Y"), p, random.randint(1, 2), price_of[p]])

# 4) Delivery orders: has TOTAL instead of unit price
with open(data_dir / "orders_delivery.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Date", "Product", "Qty", "Total"])
    for day in week:
        for _ in range(random.randint(3, 8)):
            p = random.choices(names, weights)[0]
            q = random.randint(1, 3)
            w.writerow([day.isoformat(), p, q, q * price_of[p]])

print(f"Fake pharmacy data created in: {data_dir}")