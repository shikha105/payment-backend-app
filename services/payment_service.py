from datetime import date
from config.mongodb import payments_collection

async def normalize_csv_and_insert(file_path):
    import pandas as pd

    data = pd.read_csv(file_path)
    normalized = data.fillna({"discount_percent": 0, "tax_percent": 0}).to_dict(orient="records")
    
    for entry in normalized:
        entry["total_due"] = await calculate_total_due(entry)
        entry["payee_payment_status"] = (
            "overdue" if entry["payee_due_date"] < str(date.today())
            else "due_now" if entry["payee_due_date"] == str(date.today())
            else entry["payee_payment_status"]
        )
    
    await payments_collection.insert_many(normalized)


async def calculate_total_due(payment):
    due = payment["due_amount"]
    discount = payment.get("discount_percent", 0) / 100
    tax = payment.get("tax_percent", 0) / 100
    total_due = due * (1 - discount) * (1 + tax)
    return round(total_due, 2)
