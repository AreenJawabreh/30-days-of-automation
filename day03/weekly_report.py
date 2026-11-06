"""
Day 3 - #30DaysOfAutomation (Pharmacy Edition)
Weekly pharmacy sales report: 3 CSV files -> 1 formatted Excel report.

What it does:
    1. Reads 3 sales files that have DIFFERENT column names
    2. Cleans them into one table (same columns, same date format)
    3. Joins them with the product catalog (category + stock)
    4. Builds an Excel report with 4 sheets:
         Summary      -> total revenue, items sold, sales by channel
         By Category  -> revenue per category + a bar chart
         Top 10       -> best-selling products
         Low Stock    -> products below minimum stock (in red)
         All Sales    -> every sale, for checking

Usage:
    python make_fake_data.py   (once, to create the fake data)
    python weekly_report.py
"""

from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill

BASE = Path(__file__).parent
DATA = BASE / "data"
OUTPUT = BASE / f"pharmacy_weekly_report_{datetime.now():%Y-%m-%d}.xlsx"

# ---------- 1) READ + CLEAN: make the 3 files look the same ----------

counter = pd.read_csv(DATA / "sales_counter.csv")
counter["date"] = pd.to_datetime(counter["date"], format="%Y-%m-%d")
counter["total"] = counter["qty"] * counter["unit_price"]
counter["channel"] = "Counter"

online = pd.read_csv(DATA / "orders_online.csv")
online = online.rename(columns={"order_date": "date", "item_name": "product", "quantity": "qty"})
online["date"] = pd.to_datetime(online["date"], format="%d/%m/%Y")  # different date format!
online["total"] = online["qty"] * online["price"]
online["channel"] = "Online / WhatsApp"

delivery = pd.read_csv(DATA / "orders_delivery.csv")
delivery = delivery.rename(columns={"Date": "date", "Product": "product", "Qty": "qty", "Total": "total"})
delivery["date"] = pd.to_datetime(delivery["date"], format="%Y-%m-%d")
delivery["channel"] = "Delivery"

columns = ["date", "product", "qty", "total", "channel"]
sales = pd.concat([counter[columns], online[columns], delivery[columns]], ignore_index=True)

# ---------- 2) JOIN with the product catalog ----------

products = pd.read_csv(DATA / "products.csv")
sales = sales.merge(products[["product", "category"]], on="product", how="left")
sales["category"] = sales["category"].fillna("Unknown")  # product not in catalog

# ---------- 3) CALCULATE ----------

total_revenue = sales["total"].sum()
total_items = sales["qty"].sum()

by_channel = (sales.groupby("channel")
              .agg(orders=("product", "count"), items=("qty", "sum"), revenue=("total", "sum"))
              .sort_values("revenue", ascending=False).reset_index())

by_category = (sales.groupby("category")
               .agg(items=("qty", "sum"), revenue=("total", "sum"))
               .sort_values("revenue", ascending=False).reset_index())
by_category["share_%"] = (by_category["revenue"] / total_revenue * 100).round(1)

top10 = (sales.groupby(["product", "category"])
         .agg(items=("qty", "sum"), revenue=("total", "sum"))
         .sort_values("items", ascending=False).head(10).reset_index())

low_stock = products[products["stock"] < products["min_stock"]].copy()
low_stock["to_order"] = low_stock["min_stock"] * 2 - low_stock["stock"]
low_stock = low_stock.sort_values("stock")

summary = pd.DataFrame({
    "Metric": ["Week", "Total revenue (ILS)", "Items sold", "Number of sales",
               "Best category", "Best-selling product", "Products below minimum stock"],
    "Value": [f"{sales['date'].min():%d %b} - {sales['date'].max():%d %b %Y}",
              round(total_revenue, 2), int(total_items), len(sales),
              by_category.iloc[0]["category"], top10.iloc[0]["product"], len(low_stock)],
})

# ---------- 4) WRITE to Excel with pandas ----------

all_sales = sales.sort_values("date").copy()
all_sales["date"] = all_sales["date"].dt.strftime("%Y-%m-%d")

with pd.ExcelWriter(OUTPUT, engine="openpyxl") as writer:
    summary.to_excel(writer, sheet_name="Summary", index=False)
    by_channel.to_excel(writer, sheet_name="Summary", index=False, startrow=len(summary) + 3)
    by_category.to_excel(writer, sheet_name="By Category", index=False)
    top10.to_excel(writer, sheet_name="Top 10", index=False)
    low_stock.to_excel(writer, sheet_name="Low Stock", index=False)
    all_sales.to_excel(writer, sheet_name="All Sales", index=False)

# ---------- 5) FORMAT with openpyxl ----------

wb = load_workbook(OUTPUT)
HEADER_FILL = PatternFill("solid", fgColor="1F6F5C")   # pharmacy green
HEADER_FONT = Font(bold=True, color="FFFFFF")
RED_FILL = PatternFill("solid", fgColor="F8D7DA")


def style_header(ws, row=1):
    for cell in ws[row]:
        if cell.value is not None:
            cell.fill = HEADER_FILL
            cell.font = HEADER_FONT
            cell.alignment = Alignment(horizontal="center")


def auto_width(ws):
    for col in ws.columns:
        longest = max(len(str(c.value)) if c.value is not None else 0 for c in col)
        ws.column_dimensions[col[0].column_letter].width = min(longest + 3, 45)


for ws in wb.worksheets:
    style_header(ws)
    ws.freeze_panes = "A2"
    auto_width(ws)

# Summary: second table (by channel) also gets a header + a title
ws = wb["Summary"]
channel_header_row = len(summary) + 4
style_header(ws, channel_header_row)
ws.cell(row=channel_header_row - 1, column=1, value="Sales by channel").font = Font(bold=True, size=12)

# Low Stock: whole rows in red
ws = wb["Low Stock"]
for row in ws.iter_rows(min_row=2):
    for cell in row:
        cell.fill = RED_FILL

# By Category: add a bar chart
ws = wb["By Category"]
chart = BarChart()
chart.title = "Revenue by category (ILS)"
chart.y_axis.title = "ILS"
data = Reference(ws, min_col=3, min_row=1, max_row=ws.max_row)       # revenue column
labels = Reference(ws, min_col=1, min_row=2, max_row=ws.max_row)     # category names
chart.add_data(data, titles_from_data=True)
chart.set_categories(labels)
chart.legend = None
chart.width, chart.height = 18, 9
ws.add_chart(chart, "F2")

wb.save(OUTPUT)

# ---------- 6) Print a short summary ----------

print(f"Report saved: {OUTPUT.name}")
print(f"Revenue: {total_revenue:,.0f} ILS | Items sold: {total_items} | Sales: {len(sales)}")
print(f"Best category: {by_category.iloc[0]['category']} | Top product: {top10.iloc[0]['product']}")
print(f"Low stock: {len(low_stock)} products -> {', '.join(low_stock['product'].head(5))}")