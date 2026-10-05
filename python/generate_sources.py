import json, random
from datetime import date, timedelta
import numpy as np
import pandas as pd
from faker import Faker

fake = Faker("en_CA")
random.seed(42); np.random.seed(42); Faker.seed(42)
RAW = "data/raw"

# ---------- 1. Reference data (Excel) ----------
cities = [("Montreal","Quebec"),("Laval","Quebec"),("Quebec City","Quebec"),
          ("Toronto","Ontario"),("Ottawa","Ontario"),("Mississauga","Ontario"),
          ("Calgary","Alberta"),("Vancouver","British Columbia")]
stores = pd.DataFrame([{"store_code": f"ST{i:03d}", "store_name": f"{c} Store {i}",
                        "city": c, "province": p,
                        "open_date": fake.date_between("-8y", "-2y")}
                       for i, (c, p) in enumerate(cities * 2, start=1)])

products = pd.DataFrame([
    ("P001","Phone","Smartphone Pro",1199.00),
    ("P002","Phone","Smartphone Lite",599.00),
    ("P003","Accessory","Protective Case",39.99),
    ("P004","Accessory","Screen Protector",29.99),
    ("P005","Accessory","Wireless Earbuds",179.99),
    ("P006","Accessory","Fast Charger",34.99),
    ("P007","Activation","Mobile Plan Basic",45.00),
    ("P008","Activation","Mobile Plan Premium",85.00),
    ("P009","Activation","Home Internet",75.00),
], columns=["sku","category","product_name","unit_price"])
weights = [0.08,0.10,0.15,0.12,0.05,0.12,0.18,0.10,0.10]

employees = pd.DataFrame([{"employee_id": f"E{i:04d}", "full_name": fake.name(),
                           "store_code": stores.store_code[(i-1)//4],
                           "role": "Store Manager" if i % 4 == 1 else "Sales Rep",
                           "hire_date": fake.date_between("-6y", "-1m")}
                          for i in range(1, 65)])

months = pd.date_range("2025-01-01", periods=12, freq="MS").strftime("%b-%Y")
rows = []
for s in stores.store_code:
    base = random.randint(35000, 50000)
    rows.append({"store_code": s, "metric": "Revenue",
                 **{m: round(base * random.uniform(0.9, 1.2), -2) for m in months}})
    rows.append({"store_code": s, "metric": "Activations",
                 **{m: random.randint(45, 70) for m in months}})
targets = pd.DataFrame(rows)
targets.loc[[3, 10], "store_code"] = targets.loc[[3, 10], "store_code"].str.lower() + " "

with pd.ExcelWriter(f"{RAW}/store_master.xlsx") as xw:
    stores.to_excel(xw, sheet_name="Stores", index=False)
    products.to_excel(xw, sheet_name="Products", index=False)
    employees.to_excel(xw, sheet_name="Employees", index=False)
    targets.to_excel(xw, sheet_name="Targets", index=False)

# ---------- 2. Customers (JSON) ----------
fees = {"Basic": 45, "Plus": 65, "Premium": 85}
customers = []
for i in range(1, 3001):
    plan = random.choice(list(fees))
    customers.append({
        "id": f"C{i:05d}",
        "name": fake.name(),
        "contact": {"email": fake.email() if random.random() > 0.05 else None,
                    "phone": fake.phone_number()},
        "plan": {"type": plan, "monthly_fee": fees[plan]},
        "signup_date": fake.date_between(date(2023,1,1), date(2025,12,31)).isoformat(),
        "status": random.choices(["active","churned"], [0.85, 0.15])[0],
        "home_store": random.choice(list(stores.store_code)),
    })
customers += random.sample(customers, 30)          # duplicates
with open(f"{RAW}/customers.json", "w") as f:
    json.dump(customers, f, indent=2)

# ---------- 3. Sales (CSV) ----------
n = 25000
emp_idx = np.random.randint(0, len(employees), n)
prod_idx = np.random.choice(len(products), n, p=weights)
days = np.random.randint(0, 365, n)
sales = pd.DataFrame({
    "transaction_id": [f"T{i:06d}" for i in range(1, n+1)],
    "date": [date(2025,1,1) + timedelta(days=int(d)) for d in days],
    "store_code": employees.store_code.values[emp_idx],
    "employee_id": employees.employee_id.values[emp_idx],
    "sku": products.sku.values[prod_idx],
    "quantity": np.random.choice([1,1,1,2,3], n),
    "unit_price": products.unit_price.values[prod_idx],
    "customer_id": np.random.choice([c["id"] for c in customers[:3000]], n),
})

# add mess
sales["date"] = [d.strftime("%d/%m/%Y") if random.random() < 0.10 else d.isoformat()
                 for d in sales["date"]]
m = np.random.rand(n) < 0.05
sales.loc[m, "store_code"] = sales.loc[m, "store_code"].str.lower() + " "
sales["unit_price"] = sales["unit_price"].astype(object)
m = np.random.rand(n) < 0.08
sales.loc[m, "unit_price"] = sales.loc[m, "unit_price"].map(lambda v: f"${v:.2f}")
m = np.random.rand(n) < 0.02
sales.loc[m, "quantity"] = -sales.loc[m, "quantity"]          # returns
sales["customer_id"] = sales["customer_id"].astype(object)
m = np.random.rand(n) < 0.03
sales.loc[m, "customer_id"] = None
sales = pd.concat([sales, sales.sample(200)]).sample(frac=1)  # duplicates + shuffle
sales.to_csv(f"{RAW}/sales_transactions.csv", index=False)

print(f"stores={len(stores)} products={len(products)} employees={len(employees)}")
print(f"customers={len(customers)} sales={len(sales)}")